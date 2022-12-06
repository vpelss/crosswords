#!/usr/bin/perl

#future ideas ver 3.0 meta recurse using blocks. blocks will consist of a starting word and dir and all it's crossing words

#allow sentences in words (strip out spaces)

# speed up word load use 1 line of coma, separated words??

#separate experimental options on front page

#shadow (> 1) does not work if letter only belongs to a horiz or vert word
#also fails on british

#cookies store keys / no chat

use strict;

use CGI;
use List::Util qw(shuffle);
use Time::HiRes;
use Fcntl qw(:flock SEEK_END);
use lib '.'; #nuts, PERL has changed. add local path to @INC
use vpvars;

#get setup variables the proper way
my $archivepath = $vpvars::archivepath;
my $archiveurl  = $vpvars::archiveurl;
my $scripturl  = $vpvars::scripturl;

print "Content-type: text/html\n\n";
if ( -e "processing.txt") { print"Already running."; die("$0 is already running. Exiting.\n"); };

open(my $processing, ">processing.txt") or die "Can't open : $!";
lock($processing);
&PrintResults( "Wait for it!" ) ;
$|=1; #keep it alive as long as possible

#globals
my %in; #input arguments $in{argname}

my @wordsOfLengthString = ();
#set $wordsOfLengthString[$wordLength] = "$wordsOfLengthString[$wordLength]$word,"; #build a comma delimited string of each possible word length
#my $tempMask = $mask; #of form $unoccupiedAT$unoccupied  oATo
#$tempMask =~ s/$unoccupied/\./g; #make a mask of 'GO$unoccupiedT' into 'GO.T' for the regexp
#my $wordLength = length($tempMask);
#@word_list = ($wordsOfLengthString[$wordLength] =~ /($tempMask),/g);

#must update both below at same time!
my @puzzle=();
#the puzzle with the letters inserted. array[][] of hash  $puzzle[][]->{Letter}
#input file of the form where o are blank and x is black. Letters are capatalized
#ooooxoooooxoooooxCATS
#ooooxoooooxoooooxoooo
#ooooxoooooxooooooooo
my @allMasksOnBoard;
#all words on board whether still a mask or complete $allMasksOnBoard[word number][dir 0=across 1=down] many will be undef
#start at 1 as that is the first  word number

my @letterPositionsOfWord;
#$letterPositionsOfWord[word #][dir] an array of all the word letter positions [[x,y],[x,y]....]
#set $letterPositionsOfWord[$numberCount][$dir] = [@TempLetterPositions]; #an annonomyous array reference of $x,$y pairs of all letters in the word
#get my @WordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]}
#used to find crossing words fast with @ThisSquareBelongsToWordNumber

my @ThisSquareBelongsToWordNumber;
# $ThisSquareBelongsToWordNumber[x][y][0] returns the word number this square belongs to
#set $ThisSquareBelongsToWordNumber[$xx][$yy][$dir] = $numberCount
#get my $crossingwordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$crossingWordDir]

my @nextWordOnBoard;
#all words position on board used for cycling through word placements, etc
# [{wordNumber => $wordNumber, dir => $dir},{},{}...]
#$nextWordOnBoard[]{wordNumber} $nextWordOnBoard[]{dir}

my @PositionInWord;
#$PositionInWord[x][y][dir] returns the pos of letter in the word this square belongs to starting at 0
#set $PositionInWord[$xx][$yy][$dir] = $PositionCount
#get  my $NthLetterPosition = $PositionInWord[$x][$y][$crossingWordDir]

my %wordsThatAreInserted = ();
#hash of hashes.   $wordsThatAreInserted{word} = 1 or undef
#used to prevent duplicate words on the board

my %wordLengths; #used to identify word lengths possible on the grid. $wordLength{6} = 1. we will only load words of lengths that exist!

my %WordListByMask = (); #no longer used but keep for testing. Not much faster than regex routies
# keys $wordListByMask{oYo} returns a list of all words fitting the mask
#created by taking each word, then creating a binary mask for the word and
#$wordListByMask{ooRo}{WORD}=1
#$wordListByMask{WoRo}{WORD}=1 etc
#huge database but very fast search for words fitting a mask or pattern

#------------------------------------
#letter search variables

my @nextLetterPositionsOnBoard;
#all letter position on board used for cycling through letter placements, etc
# [{x => $x, y => $y} , , ]
#$nextLetterPositionsOnBoard[]{x} $NextWordPositionsOnBoard[]{y}

my %linearWordSearch  = (); #no longer used
#very fast for finding the next possible letters in a word
#$linearWordSearch{mask}{key1 , key2} and it will return a list of keys (so there are no duplicates) representing the next possible letters.
#@letters = keys %{$linearWordSearch{$mask}};
#mask must be a prefix mask ie: TOOLooooo

#---------------------------------------------

my $padChar = 'x';
my $unoccupied = 'o';
my $padsEitherSide = 'padsEitherSide';
#$dir 0 = horiz 1 = vertical
my $dir;
my %clues;
my $hints_across;
my $hints_down;

my $biggestwordNumber;
my @OppositeDirection;$OppositeDirection[0] = 1;$OppositeDirection[1] = 0; #instead of using (not)

my $timeForCrossword;
my $recursiveCount = 1;
my $timelimit = 60 * 1 ; #only allow the script to run this long
my $debug = 0; # 1 to show debug info. could be used for attacks. leave set to 0

eval { &Main; };     # Trap any fatal errors so the program hopefully
if ($@) {  &PrintProcessing("fatal error: $@"); &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

my $game;
my $uid;
my $message;

#optimal search variables
my %wordNumberDirUsed; #$wordNumberDirUsed{$wordNumber}{$dir} so we only backtrack or note words that have been filled
my $naiveBacktrack; #a counter
my $optimalBacktrack; #a counter
my %touchingWordsForBackTrack; #global as we need to backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!
my %targetWordsForBackTrack; #global as we need to backtrack to the first  member of it we encounter. if $targetWordsForBackTrack{# source}{dir source} == undef there are NO targets!
#eg $targetWordsForBackTrack{$wordNumberSource}{$dirSource}{$crossingWordNumber}{$crossingWordDir}

#rule 1. All letters in the horizontal and vertical words (up to the failed letter) can affect the failure of laying a letter
#rule 2. All crossing words of both the horizontal and vertical words of the failed letter can affect the failure of laying a letter
#rule 3 Remove shadows by only keeping the intersection of rule 1 and 2
#rule 3 is ignored (> 1) and is nor (> 0) as it fails (over prunes) on British style crosswords
# eg: $targetLettersForBackTrack{x failed letter}{y failed letter}{x}{y} > 0 #pregenerated for speed!
my %targetLettersForBackTrack; #global as we need to backtrack to the first  member of it we encounter. if $targetLettersForBackTrack{x failed letter}{y failed letter} == undef there are NO targets!

my $oldTime;
my $grids;

sub Main {

$game = time; #this will determine the folder
$uid = $in{uid}; #facebook user ID number
if ($uid eq '') {$uid='common'} #for non facebook games

srand;

$in{TimeLimit} = 1;
$in{layouts} = 'grids';
$in{grid} = 'BigOne';
$in{grid} = '6x6';
$in{grid} = "13x13_22_112";
#$in{grid} = '5x5';
$in{grid} = "13x13_56_144";
$in{optimalbacktrack} = 1;
$in{shuffle} = 1;
$in{wordfile} = "Sympathy_31121";
$in{wordfile} = "Clues_248505";
$in{walkpath} = 'crossingwords';
#$in{walkpath} = 'GenerateNextLetterPositionsOnBoardFlat';
#$in{walkpath} = 'GenerateNextLetterPositionsOnBoardDiag';
#$in{walkpath} = 'GenerateNextLetterPositionsOnBoardDiag';
#$in{walkpath} = 'GenerateNextLetterPositionsOnBoardZigZag';

%in = &parse_form; #get input arguments. comment out for commandline running

&Process_arguments();

$timeForCrossword = time();

$message = $message . "Loading or creating grid...\n";
&PrintProcessing($message);
if ($debug ) {print "\n\nLoading or creating grid...\n\n";}
if ($in{layouts} eq 'grids')
     {
     &LoadGrid( $in{grid} );
     }

if ($in{layouts} eq 'doublespaced')
     {
     if ($debug) {print "full $in{doublespacedfull} evenodd $in{evenodd}\n\n"}
     if ($in{doublespacedfull})
          {
          &GenerateGridDoubleSpaced($in{doublespacedwidth},$in{evenodd});
          }
     else
         {
         &GenerateGridDoubleSpaced2($in{doublespacedwidth},$in{evenodd});
         }
     }

$message = $message . "Numbering grid...\n";
&PrintProcessing($message);
if ($debug ) {print time()-$timeForCrossword .  " sec Numbering grid...\n\n";}
&NumberBlankSquares();

$message = $message . "Loading word list...\n";
&PrintProcessing($message);
if ($debug ) {print time()-$timeForCrossword . " sec Loading word list...\n\n";}
&LoadWordList( $in{wordfile} );

if ($debug ) {print time()-$timeForCrossword . " sec Calculating word walk path...\n\n";}
if ($in{walkpath} eq 'crossingwords')
     {
     &GenerateNextWordPositionsOnBoardCrossing(); #good all purpose start anywhere!
     $in{mode} = 'word';
     }
if ($in{walkpath} eq 'zigzag')
     {
     &GenerateNextWordPositionsOnBoardZigZag();
     $in{mode} = 'word';
     }
if ($in{walkpath} eq 'numerical')
     {
     &GenerateNextWordPositionsOnBoardNumerical();
     $in{mode} = 'word';
     }
if ($in{walkpath} eq 'random')
     {
     &GenerateNextWordPositionsOnBoardRandom();
     $in{mode} = 'word';
     }
if ($in{walkpath} eq 'acrossthendown')
     {
     &GenerateNextWordPositionsOnBoardAcrossThenDown();
     $in{mode} = 'word';
     }
if ($in{walkpath} eq 'diagonal')
     {
     &GenerateNextWordPositionsOnBoardDiag();
     $in{mode} = 'word';
     }
if ($in{'walkpath'} eq 'GenerateNextLetterPositionsOnBoardFlat')
     {
     &GenerateNextLetterPositionsOnBoardFlat();
     $in{'mode'} = 'letter';
     my $rr = 9;
     }
if ($in{walkpath} eq 'GenerateNextLetterPositionsOnBoardZigZag')
     {
     &GenerateNextLetterPositionsOnBoardZigZag();
     $in{mode} = 'letter';
     }
if ($in{walkpath} eq 'GenerateNextLetterPositionsOnBoardDiag')
     {
     &GenerateNextLetterPositionsOnBoardDiag();
     $in{mode} = 'letter';
     }
if ($in{walkpath} eq 'GenerateNextLetterPositionsOnBoardSwitchWalk')
     {
     &GenerateNextLetterPositionsOnBoardSwitchWalk();
     $in{mode} = 'letter';
     }
if ($in{walkpath} eq 'GenerateNextLetterPositionsOnBoardSnakeWalk')
     {
     &GenerateNextLetterPositionsOnBoardSnakeWalk();
     $in{mode} = 'letter';
     }

$timeForCrossword = time(); #reset counter so we mesure time to find solution only

if ($in{optimalbacktrack}) {
     $message = $message . "Calculating Optimal Backtracks...\n";
     &PrintProcessing($message);
     if ($debug ) {print time()-$timeForCrossword .  " sec Numbering grid...\n\n";}
     &CalculateOptimalBacktracks();
     }

if ( $in{mode} eq 'word' ) {
     if ( &RecursiveWords() == 0 ) {
           $message = "\n\nFailed to fill grid Counts:$recursiveCount \n\n";
           print $message;
           PrintResults($message);
           &Quit();
           }
     }
else {
     if ( &RecursiveLetters() == 0 )
           {
           my $cnt = scalar keys %wordsThatAreInserted;
           $message = "\n\nFailed to fill grid Counts:$recursiveCount Words layed:$cnt \n\n";
           print $message;
           PrintResults($message);
           &Quit();
           }
      }

&PrintProcessing();
if ($debug ) {print time()-$timeForCrossword . " sec Done.\n\nNumbering clue list.\n\n";}

&PrintProcessing("Getting clues...");

$timeForCrossword = time(); #reset counter so we mesure time to find solution only

&Number_clue_list();

if ($debug ) {print time()-$timeForCrossword . " sec Print solved puzzle.\n\n";}
my $solved_puzzle = "";
$solved_puzzle = &print_solved_puzzle;

if ($debug ) {print time()-$timeForCrossword . " sec Print puzzle\n\n";}
my $puzzle_string = &print_puzzle;

open (DATA, "<./templates/index.html") or die("Template file /templates/index.html does not exist");
my @DATA = <DATA>;
close (DATA);
my $template_file = join('' , @DATA);

my $startx;
my $starty;
#find word 1 across or down and replace x , y in template js . fixes error when there is no letter at 0,0
for ($dir = 0; $dir < 2 ;$dir++)
      {
      #$letterPositionsOfWord[word #][dir] an array of all the word letter positions [[x,y],[x,y]....]
      if ($letterPositionsOfWord[1][$dir] != undef)
           {
           $startx = ${$letterPositionsOfWord[1][$dir]}[0][0];
           $starty = ${$letterPositionsOfWord[1][$dir]}[0][1];
           last;
           }
      }
$template_file =~ s/%startx%/$startx/g;
$template_file =~ s/%starty%/$starty/g;

$template_file =~ s/<%answers%>/$solved_puzzle/g;
$template_file =~ s/<%across%>/$hints_across/g;
$template_file =~ s/<%down%>/$hints_down/g;
$template_file =~ s/<%down%>/$hints_down/g;
$template_file =~ s/<%puzzle%>/$puzzle_string/g;
$template_file =~ s/\%archivepath\%/$archivepath/g;
$template_file =~ s/\%archiveurl\%/$archiveurl/g;
$template_file =~ s/\%scripturl\%/$scripturl/g;
$template_file =~ s/\%uid\%/$uid/g;
my $name = $in{name}; #facebook user name
$name =~ s/\%20/ /g; #get rid of %20 for spaces
$template_file =~ s/\%name\%/$name/g;

#archive the puzzle!
#my $game = time;
#$filename .= ".html";

#print '<\pre>';

$template_file =~ s/\%game\%/$game/g;
#print $template_file;

#write archive game file and directory
if (not -d ("$archivepath")) {mkdir("$archivepath")  or die("Could not create archive path $archivepath");}
if (not -d ("$archivepath/$uid")) {mkdir("$archivepath/$uid")  or die("Could not create archive path $archivepath/$uid");}
if (not -d ("$archivepath/$uid/$game")) {mkdir("$archivepath/$uid/$game")  or die("Could not create archive path $archivepath/$uid/$game");}
open (DATA, ">$archivepath/$uid/$game/index.html") or die("Could not create archive file $archivepath/$uid/$game/index.html");
print DATA $template_file;
close (DATA);
#create empty chat.txt file - cuts down on 404 errors
open (DATA, ">$archivepath/$uid/$game/chat.txt") or die("Could not create chat file $archivepath/$game/chat.txt");
close (DATA);
#create empty out.txt file - cuts down on 404 errors
open (DATA, ">$archivepath/$uid/$game/out.txt") or die("Could not create chat file $archivepath/$uid/$game/out.txt");
close (DATA);

#print a jump to game page output
#print qq|<META HTTP-EQUIV="Refresh" CONTENT="0; URL=$archiveurl/$uid/$game/?uid=$uid&name=$name">|; #name is for chat
#print qq|<META HTTP-EQUIV="Refresh" CONTENT="0; URL=$archiveurl/$uid/$game/">|;

&PrintResults( qq| Your crossword is at:<br><a href="$archivepath/$uid/$game/index.html">$archivepath/$uid/$game/index.html</a><br> | );
&Quit( qq| Done. Look at "Crossword Result after you click OK." |  );

exit;
}

sub Quit()
{
print $_[0]; #feedback to web browser
close($processing);
unlink('processing.txt');
exit;
}

sub PrintResults()
{
my $message = $_[0];
open(my $results, ">results.txt") or die "Can't open : $!";
print $results  $message;
close $results;
};

sub PrintProcessing {
my $message = $_[0];
my ($x , $y);
my $line;
my $string;
my $time;
$time =  time - $timeForCrossword;

#open(my $processing, ">processing.txt") or die "Can't open : $!";

#limit script run time!
if ($time > $timelimit)
     {
     &PrintResults( qq| Time limit exceeded | );
     &Quit( "Time limit exceeded<br>\n\n" );
     }

$string = $string . "\n";
$string = $string . "Loops per Sec: " . $recursiveCount / (time + 1 - $timeForCrossword); #print time to create crosword
$string = $string . "\n";

for ($y = 0 ; $y < $in{height} ; $y++)
      {
      for ($x = 0 ; $x < $in{width} ; $x++)
            {
            my $t = &GetXY($x,$y);
            $line = "$line$t";
            }
      $string = $string . $line;
      $string = $string . "\n";
      $line = '';
      }

for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++)
      {
      for (my $dir = 0 ; $dir < 2 ; $dir++)
            {
            my $word = $allMasksOnBoard[$wordNumber][$dir];
            #if (undef ne $word)
            if ($word)
                 {
                 #$string = $string . "$wordNumber $dir: $word \n"
                 }
            }
      }

$string = $string . "\n";
$string = $string . "Time: " . $time; #print time to create crosword
$string = $string . "\n";
$string = $string . "Loops: " . $recursiveCount; #print time to create crosword
$string = $string . "\n";
$string = $string . "Sec per Loop: " . (time - $timeForCrossword) / $recursiveCount; #print time to create crosword
$string = $string . "\n";
$string = $string .  "Loops per Sec: " . $recursiveCount / (time + 1 - $timeForCrossword); #print time to create crosword
$string = $string . "\n\n";
$string = $string . "optimalBacktrack:$optimalBacktrack naiveBacktrack:$naiveBacktrack recursive calls:$recursiveCount\n";

if ($message ne "") {
     if ($string =~ /^!/)
          {$string = "$message\n\n$string";}
     else
         {$string = "$message";}
     }

seek($processing, 0 , 0); #need to keep file open to lock it!
print $processing "$string";
};

sub Process_arguments {
#process input arguments
# Test inputs to see if they are valid and set defaults

#defaults
if ( (not $in{timeout}) or ($in{timeout} !~ /^\d+$/ ) ) { $in{timeout} = 5; };
if (not $in{wordfile}){$in{wordfile} = "./wordlists/MyClues_248505/"};

#set bounds
if  ($in{timeout} > 30)  { $in{timeout} = 30; }

$in{grid} =~ s/[^\d\w]//g;
$in{wordfile} =~ s/[^\d\w]//g;

if ( $in{TimeLimit} > 10 ) {$in{TimeLimit} = 10}
$timelimit = $in{TimeLimit} * 60;

if ( $in{SlowDown} > 5 ) {$in{SlowDown} = 5}
};

sub GenerateNextWordPositionsOnBoardCrossing
{
#start with 1 horiz.
#find all crossing words
#find all their crossing words.
#only add # and direction once!
#FIFO

my @wordLetterPositions = ();
my %alreadyInList = (); # $alreadyInList{number}{direction} = 1 if already in list
my $wordNumber = 1;
my $dir = 0;

if (not defined $allMasksOnBoard[$wordNumber][$dir] ) # oops no horizontal #1 word. go vertical
     {$dir = 1;}
my @toDoList = (); #list of words and directions to process. ((1,0) , (2,0) , .... ) shift off and push on so we do in an orderly fasion!
push @toDoList , [$wordNumber,$dir];
$alreadyInList{$wordNumber}{$dir} = 1;
push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};

while ( scalar @toDoList > 0 )
        {
        ($wordNumber , $dir) = @{ shift @toDoList };
        my @crossingWords = &GetCrossingWords( $wordNumber , $dir );
        while ( scalar @crossingWords > 0 )
                {
                ($wordNumber , $dir) = @{ shift @crossingWords };
                if ( $alreadyInList{$wordNumber}{$dir} == 1)
                     {
                     next;
                     }
                push @toDoList , [$wordNumber , $dir];
                push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
                $alreadyInList{$wordNumber}{$dir} = 1;
                }
        }
foreach my $item (@nextWordOnBoard)
         {
         if ($debug ) {print "($item->{wordNumber},$item->{dir})";}
         }
}

sub GenerateNextWordPositionsOnBoardNumerical
{
#create a sequential list in which we will lay down words. FIFO
#just go numerically 1 .. ??? alternating horiz / vert

for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++) #loop through all word numbers even if they don't exist
      {
      for (my $dir = 0 ; $dir < 2 ; $dir++) #loop through each direction even if it doesnt exist
            {
            my $word = $allMasksOnBoard[$wordNumber][$dir]; # get WORD or MASK at this crossword position
            if ($word eq undef) {next;} # if this [$wordNumber][$dir] does not exists in xword grid, find next one that does
            push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
            if ($debug ) {print "($wordNumber,$dir)";}
            }
      }
}

sub GenerateNextWordPositionsOnBoardRandom
{
#create a sequential list in which we will lay down words. FIFO
#just go numerically 1 .. ??? alternating horiz / vert

for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++) #loop through all word numbers even if they don't exist
      {
      for (my $dir = 0 ; $dir < 2 ; $dir++) #loop through each direction even if it doesnt exist
            {
            my $word = $allMasksOnBoard[$wordNumber][$dir]; # get WORD or MASK at this crossword position
            if ($word eq undef) {next;} # if this [$wordNumber][$dir] does not exists in xword grid, find next one that does
            push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
            }
      }
@nextWordOnBoard = shuffle  @nextWordOnBoard ;
my $nextWordOnBoard ;
foreach $nextWordOnBoard (@nextWordOnBoard) #loop through all word numbers
     {
     if ($debug ) {print "(${$nextWordOnBoard}{'wordNumber'} , ${$nextWordOnBoard}{'dir'} )";}
      }
}

sub GenerateNextWordPositionsOnBoardAcrossThenDown
{
#create a sequential list in which we will lay down words. FIFO
#just go numerically 1 .. ??? alternating all horiz then all vert

for (my $dir = 0 ; $dir < 2 ; $dir++) #loop through each direction even if it doesnt exist
     {
     for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++) #loop through all word numbers even if they don't exist
            {
            my $word = $allMasksOnBoard[$wordNumber][$dir]; # get WORD or MASK at this crossword position
            if ($word eq undef) {next;} # if this [$wordNumber][$dir] does not exists in xword grid, find next one that does
            push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
            if ($debug ) {print "($wordNumber,$dir)";}
            }
      }
}

sub GenerateNextWordPositionsOnBoardZigZag
{
#create a top right to bottom left list in which we will lay down words. FIFO
#zigzag alternate top right to bottom left then botom left to top right
my $x = 1;
my $y = -1;
my $divX = -1;
my $divY = 1;

do {
        #move cursor
        $x = $x + $divX;
        $y = $y + $divY;
        #test cursor position
        if ( ($x < 0) and ($y >= $in{height}) ) {#bottom left corner
               $divX = -$divX; $divY = -$divY; #change directions
               $x = 1;
               $y = $in{height} - 1;
               }
        if ( ($x >= $in{width}) and ($y < 0) ) {#top right corner
               $divX = -$divX; $divY = -$divY; #change directions
               $x = $in{width} - 1;
               $y = 1;
               #$myWidth = $in{width};
               }
        if ($x < 0){#off left
             $divX = -$divX; $divY = -$divY; #change directions
             $x = 0;
             }
        if ($y < 0){#off top
             $divX = -$divX; $divY = -$divY; #change directions
             $y = 0;
             }
        if ($x >=  $in{width}){#off right
             $divX = -$divX; $divY = -$divY; #change directions
             $x =  $in{width} - 1;
             $y = $y + 2;
             }
        if ($y >=  $in{height}){#off bottom
             $divX = -$divX; $divY = -$divY; #change directions
             $x =  $x + 2;
             $y = $in{height} - 1;
             }

        #process cursor position
        if ($puzzle[$x][$y]->{Letter} ne $padChar)
             {
             #see if we are at start of word. If sio add to list
             for (my $dir = 0 ; $dir < 2 ; $dir++)
                  {
                  my $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$dir];
                  my @wordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]};
                  if  ( ($wordLetterPositions[0][0] == $x) and ($wordLetterPositions[0][1] == $y) )
                          {
                          push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
                          if ($debug ) {print "($x,$y)word#:$wordNumber,dir:$dir | ";}
                          }
                  }
             }
        }
until ( ($x == $in{width} - 1) and ($y == $in{height} - 1) );
}

sub GenerateNextWordPositionsOnBoardDiag
{
#create a top right to bottom left list in which we will lay down words. FIFO
#zigzag alternate top right to bottom left then botom left to top right
my $x = 1;
my $y = -1;
my $divX = -1;
my $divY = 1;
my $diagCount;

@nextWordOnBoard = ();

do {
    #move cursor
    $x = $x + $divX;
    $y = $y + $divY;

    if (($x < 0) or ($y >= $in{height}) ) {
          $diagCount++;
          $x = $diagCount;
          if ($x >= $in{width} - 1) {
               $x = $in{width} - 1;
               $y = $diagCount - $x;
               }
          else {
                $y = 0;
                }
          }
    if ($debug ) {print "($x,$y)";}
    #process cursor position
    if ($puzzle[$x][$y]->{Letter} ne $padChar) {
         #see if we are at start of word. If sio add to list
         for (my $dir = 0 ; $dir < 2 ; $dir++)
                  {
                  my $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$dir];
                  my @wordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]};
                  if  ( ($wordLetterPositions[0][0] == $x) and ($wordLetterPositions[0][1] == $y) )
                          {
                          push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
                          if ($debug ) {print "($x,$y)word#:$wordNumber,dir:$dir | ";}
                          }
                  }
         }
    }
until ( ($x >= $in{width} - 1) and ($y >= $in{height} - 1) );
}

sub GenerateGridDoubleSpaced()
{
#input width (which gives height) and oddEven style
#output a text array of width and height and create full double space pattern
#also set globals $in{width} and $in{height}

my $width = $_[0];
my $oddEven = $_[1] | 0;

$in{width} = $width;
$in{height} = $width;

#build a basic double spaced grid
for (my $y = 0 ; $y < $width ; $y++)
     {
     for (my $x = 0 ; $x < $width ; $x++)
          {
          $puzzle[$x][$y]->{Letter} = $unoccupied; # assume, then change as required
          if ( ( ($y % 2) != $oddEven) and ( ($x % 2) != $oddEven) )
              {
              $puzzle[$x][$y]->{Letter} = $padChar;
              }
          }
     }
}

my %breadCrumbs;
sub GenerateGridDoubleSpaced2()
{#random british grid generator
#fill with whitespace and pads then add pads one at a time. If pad separates any area, undo and try again.
#fill all joining squares with breadcrumbs using recursion. If all surrounding whitespace has a breadcrumb then there are no islads of white
#if words nsew are > 2 try again

my $width = $_[0];
my $oddEven = $_[1] | 0;
my ($x , $xx , $y , $yy);
my @unoccupiedNSEWWhitespace;
my $wordSizeH;
my $wordSizeV;

$in{width} = $width;
$in{height} = $width;

&GenerateGridDoubleSpaced($width,$oddEven);

my $padCells;
my $whiteCells;
#calculate  density
for ($y = 0 ; $y < $in{height} ; $y++)
      {
      for ($x = 0 ; $x < $in{width} ; $x++) {
            if ($puzzle[$x][$y]->{Letter} eq $padChar)
                       {$padCells++;}
            if ($puzzle[$x][$y]->{Letter} eq $unoccupied)
                       {$whiteCells++;}
            }
      }
my $totalCells = $in{height} * $in{width};
my $time_to_quit = time() + 3; #5 seconds!
MAINLOOP: while (time() < $time_to_quit)
       {
       $x = int(rand( $in{width} ));
       $y = int(rand( $in{height} ));

       if ( $in{doublespacedpercentage} > int(100 * ($totalCells - $padCells) / $totalCells) )
            {
            last; #we have reached black pad percentage quota
            }

       #already is a pad
       if ( $puzzle[$x][$y]->{Letter} eq $padChar )
             {
             next;
             }

       #place pad first so we can calculate word sizes, remove if fail!
       $puzzle[$x][$y]->{Letter} = $padChar;
       $padCells++;

       #get first whitespace around proposed pad space
       %breadCrumbs = (); #start fresh
       @unoccupiedNSEWWhitespace = &ReturnLocalWhiteSquares($x,$y);

       #see if surrounded by pads - next!
       if (scalar @unoccupiedNSEWWhitespace == 0)
           {
           $puzzle[$x][$y]->{Letter} = $unoccupied;
           $padCells--;
           next;
           }

       #take 1st local whitespace and run with it
       $xx = $unoccupiedNSEWWhitespace[0][0];
       $yy = $unoccupiedNSEWWhitespace[0][1];

       &BreadCrumbAllWhiteFromHere($xx,$yy); #mark all touching whitespace starting from either NSEW

       #check each local surrounding whitespace for a breadcrumb  and check for legal word sizes
       foreach my $item (@unoccupiedNSEWWhitespace)
                {
                $xx = $item->[0];
                $yy = $item->[1];

                #check to see if both horiz and vert word size are valid
                $wordSizeH = &calcWordSize( $xx ,$yy , 0);
                $wordSizeV = &calcWordSize( $xx ,$yy , 1);
                if ( $wordSizeH == 1 and $wordSizeV == 1 )
                     {
                     $puzzle[$x][$y]->{Letter} = $unoccupied;
                     $padCells--;
                     next MAINLOOP;
                     }
                if ( not($wordSizeH == 1) and ($wordSizeH < 3) )
                     {
                     $puzzle[$x][$y]->{Letter} = $unoccupied;
                     $padCells--;
                     next MAINLOOP;
                     }
                if ( not($wordSizeV == 1) and ($wordSizeV < 3) )
                     {
                     $puzzle[$x][$y]->{Letter} = $unoccupied;
                     $padCells--;
                     next MAINLOOP;
                     }
                #check to see if bread crumb exists for all surrounding whitespace or next
                if ( $breadCrumbs{$xx}{$yy} != 1 )
                      {
                      $puzzle[$x][$y]->{Letter} = $unoccupied;
                      $padCells--;
                      next MAINLOOP;
                      }
                }
       }
};

sub BreadCrumbAllWhiteFromHere()
{
#given a starting location $unoccupied, mark all adjoining whitespace with breadcrumbs and when done, return
my $x = $_[0];
my $y = $_[1];
my @unoccupiedNSEWWhitespace = ();

$breadCrumbs{$x}{$y} = 1; #mark visited

#get all $unoccupied and unvisited local pads around x y and push to a list
@unoccupiedNSEWWhitespace = &ReturnLocalWhiteSquares($x,$y);

if ( (scalar @unoccupiedNSEWWhitespace) == 0) #surrounded by pads or already visited
            {
            return;  #start of the end
            }

foreach my $item (@unoccupiedNSEWWhitespace)
        {
         #choose next adjoining white space
         $x = $item->[0];
         $y = $item->[1];
         #continue recursive journey
         &BreadCrumbAllWhiteFromHere($x,$y);
        }
};

sub ReturnLocalWhiteSquares()
{
#give a sqare and return a list of ([x y] [x y] [x y] ....) of NSEW white squares
my @unoccupiedNSEWWhitespace;
my ($x , $y);

#check N
$x = $_[0];
$y = $_[1] - 1;
if ( not &outsideCrossword($x,$y) and ($puzzle[$x][$y]->{Letter} eq $unoccupied) and ($breadCrumbs{$x}{$y} != 1))
     {
     push @unoccupiedNSEWWhitespace , [$x,$y];
     }
#check S
$x = $_[0];
$y = $_[1] + 1;
if ( not &outsideCrossword($x,$y) and ($puzzle[$x][$y]->{Letter} eq $unoccupied) and ($breadCrumbs{$x}{$y} != 1))
     {
     push @unoccupiedNSEWWhitespace , [$x,$y];
     }
#check E
$x = $_[0] + 1;
$y = $_[1];
if ( not &outsideCrossword($x,$y) and ($puzzle[$x][$y]->{Letter} eq $unoccupied) and ($breadCrumbs{$x}{$y} != 1))
     {
     push @unoccupiedNSEWWhitespace , [$x,$y];
     }
#check W
$x = $_[0] - 1;
$y = $_[1];
if ( not &outsideCrossword($x,$y) and ($puzzle[$x][$y]->{Letter} eq $unoccupied) and ($breadCrumbs{$x}{$y} != 1))
     {
     push @unoccupiedNSEWWhitespace , [$x,$y];
     }

return @unoccupiedNSEWWhitespace;
};

sub Number_clue_list {
my $x = -1;
my $y = -1;
my @word_sort;
my $wordNumber;
my $positionPair;
my @wordLetterPositions;
my $wordLetterPositions;
my @temp;
my $word;
my $hints;
my $dir;
my @clues;

for ($dir=0 ; $dir < 2 ; $dir++)
     {
     $hints = '';
     for ($wordNumber=1 ; $wordNumber <= $biggestwordNumber ; $wordNumber++)
           {
           $word = $allMasksOnBoard[$wordNumber][$dir];

           if ($word ne undef)
                {
                #get clue(s)
                my $first2Leters = substr $word , 0 , 2;
                my $directory = "./wordlists/$in{wordfile}/clues/";
                #my $filename = "$directory"."_"."$word\.clu";
                my $filename = "$directory"."_"."$first2Leters\.clu";
                open (DATA, "<$filename") or die("Word file $filename does not exist");
                my $line;
                @clues = ();
                foreach $line (<DATA>)
                         {
                         #filter for just word
                         #my $lineWord;
                         #my $lineClue;
                         (my $lineWord , my $lineClue) = split /\|/ , $line;
                         if ($lineWord eq $word)
                              {
                              push (@clues , $lineClue);
                              }
                         }
                close DATA;

                my $clue = $clues[int(rand(scalar @clues))];
                $clues{$word} = $clue;

                $wordLetterPositions = &javascriptArrayFromLetterPositions(@{$letterPositionsOfWord[$wordNumber][$dir]}); #clear last one
                $x = $letterPositionsOfWord[$wordNumber][$dir]->[0]->[0];
                $y = $letterPositionsOfWord[$wordNumber][$dir]->[0]->[1];
                my $temp = qq| <font size=-1><a href='http://www.google.ca/search?q=$word' target='_blank'>google</a></font> |;

                #<font><i><A ONCLICK="if (this.innerHTML=='show') {this.innerHTML='$word'} else {this.innerHTML='show'}" HREF="\#self">show</A></i></font>
                $hints .= qq|
                    $wordNumber\. <a href="\#self" id="$word" class="clues" ONCLICK="choose('$word' , $x , $y , [$wordLetterPositions]);">$clues{$word}</a>
                    &nbsp;<font size=-2><a href="http://www.google.ca/search?q=$clues{$word}" target="_blank">google</a></font>
                    &nbsp;&nbsp;&nbsp;&nbsp;

                    <font><i>
                    <span id='show$word' ONCLICK="hide2('show$word');show2('clue$word');show2('google$word');" >
                     <a href="#" ONCLICK="return false">show</a>
                     </span>
                    <span id='clue$word' ONCLICK="hide2('clue$word');hide2('google$word');show2('show$word');" >
                     <a href="#" ONCLICK="return false">$word</a>
                     </span>
                    <span id='google$word' >
                     <font size=-2><a href="http://www.google.ca/search?q=$word" target="_blank">google</a></font>
                     </span>
                    <i></font>
                    </br>
                    <script>hide2('clue$word');hide2('google$word');</script>
                    |;
               }
          }
     if ($dir == 0) {$hints_across = $hints}
     if ($dir == 1) {$hints_down = $hints}
     }
}

sub LoadGrid
{
my $filename = $_[0];
my ($x , $y);
$in{height} = 0;
$in{width} = 0;
my $square;
my $temp = 0;

$filename = "./grids/$filename.txt";
open (DATA, "<$filename") or die("Grid file $filename does not exist");
foreach my $line (<DATA>)
         {
        $x = 0;
        chomp($line);
         my @squares = split(// , $line);
         foreach $square (@squares)
                 {
                 $puzzle[$x][$y]->{Letter} = $square; #should be an x or a o.
                 $x++;
                 }
         if ($x > $temp) {$temp = $x};
         $y++;
         }
close (DATA);

$in{width} = $temp; #store largest x width line 1 to width
$in{height} = $y; #store largest y height 1 to height

if ($debug ) {print "width:$in{width} height:$in{height}\n\n";}

#only allow square grids. If not, force it to be square!
#make all lines same width, if no x or o then pad with $padChar at end of line
for ($y = 0 ; $y <$in{height} ; $y++)
     {
     for ($x = 0 ; $x <$in{width} ; $x++)
           {
           if ($puzzle[$x][$y]->{Letter} eq '') #there is no x or o so our line is shorter than the rest
                {$puzzle[$x][$y]->{Letter}=$padChar}
           }
     }
}

sub NumberBlankSquares
{
my ($x , $xx);
my ($y , $yy);
my $wordLength;
my $numberCount;
my $acrossWord;
my $dir;
my @TempLetterPositions;
my $PositionCount;
my $blankWord;
my $atEdge;
my $crossingCells;
my $totalCells;
my $whiteCells;
my $padCells;
my $wasAnAcrossWord = 0;

for ($y = 0 ; $y < $in{height} ; $y++)
      {
      for ($x = 0 ; $x < $in{width} ; $x++)
            {
            $wasAnAcrossWord = 0; #assume not
            for ($dir = 0 ; $dir < 2 ; $dir++) #for both across 0 and down 1 words
                  {
                  $wordLength = &calcWordSize($x,$y,$dir);
                  #if ($wordLength > 2) #words of length 0 are returned if we are on a pad character. ignore. also counts 1 letter words and 2 letter word
                  if ($wordLength >= 2) #words of length 0 are returned if we are on a pad character. ignore. also counts 1 letter words and 2 letter word
                    {
                    $wordLengths{$wordLength} = 1; #mark globally that there is a word of this length
                    }
                  $atEdge = 0; #are we on a grid edge square?
                  if (($dir == 0) and ($x == 0)) {$atEdge = 1;} #across word edge
                  if (($dir == 1) and ($y == 0)) {$atEdge = 1;} #down word edge
                  if ( ($wordLength >= 2) and ( ($puzzle[$x - ($OppositeDirection[$dir])][$y - $dir]->{Letter} eq $padChar) or $atEdge ) ) #this is the start of a word if we are 1. at an edge andlooking in right direction 2. pad before the character in the right direction
                         {#start of either an acrross, down or both word
                         if ($dir == 0) {
                              $numberCount++; # always increase numbercount on across words
                              $wasAnAcrossWord = 1; # we had an across word. so if we have a down word also, don't increase the numberCount
                              };
                         if ( ($dir == 1) and ($wasAnAcrossWord == 0) ) {$numberCount++}; #only increase down word if it is a lone down word and not shared with an across word
                         #if ($wasAnAcrossWord == 0) {$numberCount++} #we have not registered an across word at this square yet. so this must be an across square and therefore we increase the number count as only a down will share the count number
                         #build PositionInWord , LetterPositions , wordNumbers
                         @TempLetterPositions = &LetterPositionsOfWord($x,$y,$dir,$wordLength); #get all the letter positions in this word
                         $PositionCount = 0;
                         $blankWord = '';
                         foreach my $letterPosition (@TempLetterPositions)
                                 {
                                 $xx = $letterPosition->[0];
                                 $yy = $letterPosition->[1];
                                 $ThisSquareBelongsToWordNumber[$xx][$yy][$dir] = $numberCount;
                                 $PositionInWord[$xx][$yy][$dir] = $PositionCount;
                                 $PositionCount++;
                                 $blankWord = "$blankWord$unoccupied";
                                 }
                         $allMasksOnBoard[$numberCount][$dir] = $blankWord;
                         $letterPositionsOfWord[$numberCount][$dir] = [@TempLetterPositions]; #an annonomyous array reference of $x,$y pairs of all letters in the word
                         }
                  }

            }
      }

#calculate interlock and density
for ($y = 0 ; $y < $in{height} ; $y++)
      {
      for ($x = 0 ; $x < $in{width} ; $x++)
            {
            #for ($dir = 0 ; $dir < 2 ; $dir++) #for both across 0 and down 1 words
                  {
                  if ( exists($ThisSquareBelongsToWordNumber[$x][$y][0]) and exists($ThisSquareBelongsToWordNumber[$x][$y][1]) )
                       {$crossingCells++;}
                  if ($puzzle[$x][$y]->{Letter} eq $padChar)
                       {$padCells++;}
                  if ($puzzle[$x][$y]->{Letter} eq $unoccupied)
                       {$whiteCells++;}
                  }
            }
      }
$totalCells = $in{height} * $in{width};
my $interlock = 100 * $crossingCells / $totalCells;
$interlock = sprintf "%.1f", $interlock;
my $density = 100 * $whiteCells / $totalCells;
$density = sprintf "%.1f", $density;

$biggestwordNumber = $numberCount;
if ($debug ) {print "Grid has words of lengths : ";}
foreach $wordLength (keys %wordLengths)
         {
         if ($debug ) {print "$wordLength ,";}
         }
if ($debug ) {print "\nDensity:$density\% , Interlock:$interlock\% , Crossing:$crossingCells , White:$whiteCells , Total:$totalCells \n\n";}
};

sub CalculateOptimalBacktracks()
{
#%touchingWordsForBackTrack; #global as we need to backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!

#rule 1. All letters in the horizontal and vertical words (up to the failed letter) can affect the failure of laying a letter
#rule 2. All crossing words of both the horizontal and vertical words of the failed letter can affect the failure of laying a letter
#rule 3 Remove shadows by only keeping the intersection of rule 1 and 2
# $targetLettersForBackTrack{x failed letter}{y failed letter}{x}{y} = 1 #pre-generated for speed!
my ($x , $y , $xx , $yy , $letterPosition);
my @upToXY ; #this will be the shifter part we will check to see if there is an
      #optimal target in the backtrack. We need 2 as one needs to be prisine so we can reassign it to @nextLetterPositionsOnBoard
my  @upToXYTemp ;
my @wordLetterPositions;
my $cellPosition;

my %wordPosition;
my $wordNumber;
my $dir;
my @upToCurrentWord;
my @upToCurrentWordTemp;
my @wordPositions;

if ($in{mode} eq "letter") {
     while (scalar @nextLetterPositionsOnBoard != 0) {
            $cellPosition =  shift @nextLetterPositionsOnBoard ; #remove next letter position
            $x = ${$cellPosition}{x};
            $y = ${$cellPosition}{y};
            #push @upToXY , {x => $x , y => $y};  # put it on @upToXY
            push @upToXY , $cellPosition;  # put it on @upToXY
            if ($debug) {print "Letter Pos $x,$y dir $dir\n"}
            #increase $targetLettersForBackTrack for all letter positions in word
            @wordLetterPositions = &MarktargetLettersForBackTrackFromWordLetterPositions($x,$y,$x,$y,$dir);
            #increase $targetLettersForBackTrack for all letter positions in crossing words
            if ($debug) {print "crossing\n "}
            foreach $letterPosition (@wordLetterPositions) {
                     $xx = $letterPosition->[0];
                     $yy = $letterPosition->[1];
                     if ($debug) {print "for word letter pos $xx $yy : "}
                     &MarktargetLettersForBackTrackFromWordLetterPositions($x , $y , $xx , $yy , $OppositeDirection[$dir]);
                     }
            if ($debug) {print "\n\n"}
            #Walk back from $x , $y if no optimal targets, then optimal will not work here. So delete %targetLettersForBackTrack{$x}{$y}
            @upToXYTemp = @upToXY; #maintain @upToXY
            pop @upToXYTemp; #remove the square we are on, as it will never be a bactrack target. it is the source
            my $trigger = 1 ; #assume no optimal backtrack targets
            foreach my $item (@upToXYTemp) { #try and prove wrong
                    $xx = ${$item}{x};
                    $yy = ${$item}{y};
                    if ( $targetLettersForBackTrack{$x}{$y}{$xx}{$yy} != undef ) {
                        $trigger = 0; #found at least one target
                        last;
                        }
                    }
            if ($trigger == 1) {
                 undef $targetLettersForBackTrack{$x}{$y}; #set to undef so it will alet us later there are no backtrack targets.
                 if ($debug) { print "optimal fail at $x $y no backtrack targets. \$targetLettersForBackTrack{$x}{$y} now equals $targetLettersForBackTrack{$x}{$y}\n"};
                 }
            }
     @nextLetterPositionsOnBoard = @upToXY; #IMPORTANT restore @nextLetterPositionsOnBoard
     }

if ($in{mode} eq 'word') {
     while (scalar @nextWordOnBoard != 0) {
            %wordPosition =  %{ shift @nextWordOnBoard }; #keep in subroutine unchaged as we may need to unshift on a recursive return
            $wordNumber = $wordPosition{wordNumber};
            $dir = $wordPosition{dir};
            push @upToCurrentWord , {%wordPosition} ;  # put it on @upToCurrentWord
            if ($debug) {print "Word # $wordNumber dir $dir\n"}
            #increase $targetWordsForBackTrack for all crossing words
            &MarkTargetBackTrackWordsThatCross($wordNumber,$dir,$wordNumber,$dir);

            #increase $targetWordsForBackTrack for all crossing words that crossed our words
            #ignore double crossing if simple mask search
            if (not $in{simplewordmasksearch}) {
                if ($debug) {print "crossing\n "}
                @wordPositions = &GetCrossingWords($wordNumber,$dir);
                foreach my $wordPosition (@wordPositions) {
                     my $wordNumberCrossing = ${$wordPosition}[0];
                     my $dirCrossing = ${$wordPosition}[1];
                     if ($debug) {print "for word letter pos $xx $yy : "}
                     &MarkTargetBackTrackWordsThatCross($wordNumber,$dir,$wordNumberCrossing,$dirCrossing);
                     }
                if ($debug) {print "\n\n"}
                }

            #Walk back from # dir if no optimal targets, then optimal will not work here. So delete %targetWordsForBackTrack{#}{dir}
            @upToCurrentWordTemp = @upToCurrentWord; #maintain @upToCurrentWord
            pop @upToCurrentWordTemp; #remove the word we are on, as it will never be a bactrack target. it is the source
            my $trigger = 1 ; #assume no optimal backtrack targets
            foreach my $item (@upToCurrentWordTemp) { #try and prove wrong
                    my $wordNumberTarg = ${$item}{wordNumber};
                    my $dirTarg = ${$item}{dir};
                    if ( $targetWordsForBackTrack{$wordNumber}{$dir}{$wordNumberTarg}{$dirTarg} != undef ) {
                        $trigger = 0; #found at least one target
                        last;
                        }
                    }
            if ($trigger == 1) {
                 undef $targetWordsForBackTrack{$wordNumber}{$dir}; #set to undef so it will alet us later there are no backtrack targets.
                 #$targetLettersForBackTrack{$x}{$y} = ();
                 if ($debug) { print "optimal fail at $x $y no backtrack targets. \$targetLettersForBackTrack{$x}{$y} now equals $targetLettersForBackTrack{$x}{$y}\n"};
                 }

            }
     @nextWordOnBoard  = @upToCurrentWord; #IMPORTANT restore @nextWordOnBoard
     }
}

sub MarkTargetBackTrackWordsThatCross()
{
#input: word number and direcction
#find all crossing words and for each:
#output: global hash (quick access) of words number and direction of words that are backtrack targets
# $targetWordsForBackTrack{# of source}{dir of source}{# target}{dir target} = 1

my $wordNumberSource = $_[0];
my $dirSource = $_[1];

my $wordNumber = $_[2];
my $dir = $_[3];

my @crossingWords;
my $crossingWord;
my $crossingWordDir;
my $crossingWordNumber;

@crossingWords = &GetCrossingWords($wordNumber,$dir);
foreach $crossingWord (@crossingWords)  {
         $crossingWordNumber = ${$crossingWord}[0];
         $crossingWordDir = $OppositeDirection[$dir];
         $targetWordsForBackTrack{$wordNumberSource}{$dirSource}{$crossingWordNumber}{$crossingWordDir}++;
         }
}

sub MarktargetLettersForBackTrackFromWordLetterPositions()
{
#MarktargetLettersForBackTrackFromWordLetterPositions(x opt start , y opt start , x calc , y calc , dir calc)
#input start with $x,$y for optimized start position and $x $y for calculation start position and letter position and $dir
#increase value in global $targetLettersForBackTrack{$x}{$y}{$xx}{$yy}
#return word letter positions [[x0,y0],[x1,y1],.....]

my $x = shift @_;
my $y = shift @_;
my $xx = shift @_;
my $yy = shift @_;
my $dir = shift @_;

my ($xxx , $yyy , $letterPosition);

my $wordNumber;
my @wordLetterPositions;

$wordNumber = $ThisSquareBelongsToWordNumber[$xx][$yy][$dir];
if ($wordNumber == undef) {return()}
@wordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]};

if ($debug) {print "letter positions:\n"}
foreach  $letterPosition (@wordLetterPositions) {
         $xxx = $letterPosition->[0];
         $yyy = $letterPosition->[1];
         $targetLettersForBackTrack{$x}{$y}{$xxx}{$yyy}++ ;
         if ($debug ) {print "\$targetLettersForBackTrack{$x}{$y}{$xxx}{$yyy}  = $targetLettersForBackTrack{$x}{$y}{$xxx}{$yyy}\n"}
         }
if ($debug ) {print "\n"}
return  @wordLetterPositions;
}

sub LoadWordList {
my $filename = $_[0];
my $line;
my $word;
my $clue;
my $wordLength;
my $mask;
my $lineCount;
my $t = time();
my %wordsOfLength;
my $wordCount;

my $directory = "./wordlists/$in{wordfile}/words/";
#read word and clue file
if (not -d $directory) {die "directory $directory does not exist"};

=pod
#build binary mask lists for all the word lengths 3-15
# @{ $binaryMasks{ $numberOfLetters ) }
for ( my $numberOfLetters = 2 ; $numberOfLetters < 21 ; $numberOfLetters++)
      {
      if ( $wordLength{$numberOfLetters} != 1 ) {next;}; #skip words that are of a length that are not on grid
      for ($decimal = 0 ; $decimal < 2 ** $numberOfLetters ; $decimal++)
            {
            my $mask = sprintf "%0*b" , $numberOfLetters , $decimal;   #convert to binary# ensure it is a string and has leading 0's
            push @{ $binaryMasks{$numberOfLetters} } , "$mask";
            }
      }
=cut

#new routine just loads word files of requested word lengths
#work files were separated earlier
foreach $wordLength ( keys %wordLengths)
         {
         $message = $message . "Loading words of length $wordLength...\n";
         &PrintProcessing($message);

         $filename = "$directory$wordLength\.txt";
         #$filename = "$directory/all.txt";
         open (DATA, "<$filename") or &Quit( "Word file $filename does not exist" );
         print '.'; #help keep alive on big loads

         foreach $word (<DATA>)
                  {
                  $word =~ s/\n//g; #remove line return
                  $word =~ s/\r//g; #remove line return
                  if ($word eq '') {next} #blank line. toss
                  $lineCount++;
                  $word = uc($word); #all words must be uppercase for standard, display and search reasons.
                  $wordsOfLength{$wordLength}++; #global var for statistics

                  #build $wordsOfLengthString[$wordLength] string
                  if ($wordsOfLengthString[$wordLength] eq '') {$wordsOfLengthString[$wordLength] = ','} #start string of words with a coma
                  $wordsOfLengthString[$wordLength] = "$wordsOfLengthString[$wordLength]$word,"; #build a comma delimited string of each possible word length

                  #letter by letter build here
                  my @lettersInWord =  split('' , $word);
                  my $letterPosition = 0;
                  #prep for new fast linear word search : $linearWordSearch{mask}
                  $mask = $word;
                  $mask =~ s/\S/o/g; #build a mask with ooooooooo of wordlength
                  foreach my $letter (@lettersInWord)
                           {
                           #build new fast linear word search : $linearWordSearch{mask}
                           $linearWordSearch{$mask}{ substr($word,$letterPosition,1) } = 1 ; #add letter for $letterPosition to set of hash keys for this $mask
                           substr ( $mask , $letterPosition , 1 , $letter); #change mask with next letter added to it Cooo to COoo
                           $letterPosition++;
                           }
=pod
                   foreach $mask (@{ $binaryMasks{$wordLength} })
                            {
                            #convert RICKETS into ooooooS oooooTo oooooTS , etc
                            #from : http://stackoverflow.com/questions/1871092/masking-a-string-in-perl-using-a-mask-string
                            #$str =~ s/(.)/substr($mask, pos $str, 1) eq 'o' ? $1 : 'x'/eg;
                            $maskedWord = $word;
                            $maskedWord =~ s/(.)/substr($mask, pos($maskedWord) , 1) eq '0' ? $1 : 'o'/eg; #mask the word with our boolean mask. replace all 0 positions in $mask with a o in our $maskedWord
                            #then we add RICKETS to ${ooooooS}{RICKETS} ${oooooTo}{RICKETS} ${oooooTS}{RICKETS} , etc
                            #$wordListByMask{$maskedWord}{$word} = '1'; # the keys built by $word are the list
                            push @{$wordListByMask{$maskedWord}} , $word;
                            #@kkeys = keys %{$wordListByMask{$maskedWord}};
                            }
=cut
                  }
         close (DATA);
         }

#done loading words. Let's calculate some statistics
foreach my $length (sort keys %wordsOfLength)
     {
     if ($debug ) {print "$length : $wordsOfLength{$length}\n";}
     $wordCount = $wordCount + $wordsOfLength{$length};
     }

my $tt = time() - $t;
if ($debug ) {print "$lineCount lines and $wordCount words loaded in $tt sec \n\n";}
}

my %wordBackTrackSource; #set to () to stop backtrack and set for backtrack $letterBackTrackSource{x} and  $letterBackTrackSource{y}
sub RecursiveWords()
{
#recursive try to lay down words using @nextWordOnBoard, will shift off, store and unshift if required
#store locally the possible words in  @possibleLetterLists
#in just the next index in a list (@NextWordPositionsOnBoard) of word position we are trying to fill

my @wordsThatFit;
my $popWord;

%wordBackTrackSource = (); #clear global indicating that we are moving forward and have cleared the backtrack state

if (scalar @nextWordOnBoard == 0) {return 1}; #if we have filled all the possible words, we are done. This breaks us out of all recursive  success loops
my %wordPosition =  %{ shift @nextWordOnBoard }; #keep in subroutine unchaged as we may need to unshift on a recursive return
my $wordNumber = $wordPosition{wordNumber};
my $dir = $wordPosition{dir};

#get all possible words for mask
my $mask = $allMasksOnBoard[$wordNumber][$dir]; # get WORD or MASK at this crossword position

if ($in{simplewordmasksearch}) {
     #simple one. 0.0002 sec a call.  better for less crosslinks?
     #ignore crossing words as future mask checks will find the failures/errors. not true for some walks as there msay be no crossword checking!
     #it will only work well with alternating across and down checks
      if ($in{shuffle}) {
           @wordsThatFit = shuffle &WordsFromMask($mask);
           }
      else {
           @wordsThatFit = sort {$b cmp $a} &WordsFromMask($mask);
            }
     }
else {
      #complex one 0.05 sec a call. better for more crosslinks?
      my @possibleLetterLists = &LetterListsFor($wordNumber , $dir);
      if ($in{shuffle}) {
           @wordsThatFit = shuffle &WordsFromLetterLists(@possibleLetterLists);
           }
      else {
            @wordsThatFit = sort {$b cmp $a} &WordsFromLetterLists(@possibleLetterLists);
            }
      }

$recursiveCount++; #count forward moving calls

my $success = 0;
while ($success == 0)
        {
        if (scalar @wordsThatFit == 0) #are there any possible words? If no backtrack
              {
              #fail to find a list of words going forward
              #or we are out of pop words in a recursion (while loop) so go back a word
              unshift @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
              #get/set global touchingWords and backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!
              if ($in{optimalbacktrack} == 1) {
                   $wordBackTrackSource{wordNumber} = $wordNumber;
                   $wordBackTrackSource{dir} = $dir;
                    }
              $wordNumberDirUsed{$wordNumber}{$dir} = undef;
              return 0;
              }; #no words so fail

        #try the next word that fit in this location
        $popWord = pop @wordsThatFit;
        if ($wordsThatAreInserted{$popWord} == 1) #this word is already used. fail
                  {
                 #&placeMaskOnBoard($wordNumber , $dir , $mask);  #is this required? we have not layed pop word
                 next; #choose another word ie. pop
                  }
        else #place word
                 {
                 &placeMaskOnBoard($wordNumber , $dir , $popWord);
                 $wordsThatAreInserted{$popWord} = 1;
                 $wordNumberDirUsed{$wordNumber}{$dir} = 1;
                 }

        if (time() > $oldTime + 2) #print every 3 seconds
              {
              if ($debug ) {print time()-$timeForCrossword . " sec wordNumber:$wordNumber , dir:$dir $popWord optimalBacktrack:$optimalBacktrack naiveBacktrack:$naiveBacktrack recursive calls:$recursiveCount\n";}
              else {print '.';} # otherwise apache timeout directive limit is reached
              &PrintProcessing();
              $oldTime = time();
              }

        if ( $in{SlowDown} > 0 ) {sleep ($in{SlowDown})}

        #attempt to lay next word
        $success = &RecursiveWords(); #lay next word in the next position
        if ($success == 1){return 1;}; #board is filled, return out of all recursive calls successfuly
#---------------
        #if we are here, the last recursive attempt to lay a word failed. So we are backtracking.
        #returning from last word which failed

        delete $wordsThatAreInserted{$popWord}; #allow us to reuse word
        #failed so reset word to previous mask
        &placeMaskOnBoard($wordNumber , $dir , $mask);

        if ($in{optimalbacktrack} == 0)
             {
             %wordBackTrackSource = (); #stop optimal recursion?
             }

        #optimal backtrack check and processing
        if (%wordBackTrackSource != ())
             {
              #we are doing an optimal backtrack
              if ($targetWordsForBackTrack{$wordBackTrackSource{wordNumber}}{$wordBackTrackSource{dir}}{$wordNumber}{$dir} > 0) { #if it is equal to one, it is in a 'shaddow' and does not affect the failed letter
                   #we have hit the optimal target. turn off optimal backtrack
                   %wordBackTrackSource = ();
                   }
              else {
                    #still in optimal backtrack so keep going back
                    unshift @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
                    $optimalBacktrack++;
                    $wordNumberDirUsed{$wordNumber}{$dir} = undef;
                    return 0;
                    }
              }

        $naiveBacktrack++;
        next; #naive backtrack
        }

die('never get here'); #never get here
}

my %letterBackTrackSource; #set to () to stop backtrack and set for backtrack $letterBackTrackSource{x} and  $letterBackTrackSource{y}
sub RecursiveLetters()
{
#recursive try to lay down letters using @nextLetterPositionsOnBoard, will shift of, store and unshift if required
#store locally the possible letters in  @possibleLetter
#the next index in the list (@nextLetterPositionsOnBoard) is the next letter position we are trying to fill

#recurse if we can't find possible letters (going forward) or run out of possible letters
#next / loop if we can't lay a letter (word already used) and we have more possible letters to pick from
#anytime we next / loop set to $unoccupied (just in case)
#anytime we recurse back (can't lay a letter or run out) a square we must unshift @nextLetterPositionsOnBoard , {x => $x, y => $y}; and return 0
#after we have returned from a failed letter down the road, set $unoccupied (to try another letter) and next / loop to see if there are anymore possible letters for this square

#note optimal recursion will not work if upper letter is part of a horizontal word
#the reason is that we may be bactracking due to a later letter in the upper horizontal word.
#If we wipe that word out without trying ALL the cobinations in that upper word we may be missing possible words in the horizontal word we are working on now
#an exception is if it is the last letter of a horizontal word
#so: only optimal up if:
     #1. the upper target letter it is not part of a horeizontal word
     #2. the upper target letter is the last letter in a horizontal word
     #3. the letter that failed is in a single vertical word

my @lettersThatFit;
my $popLetter;
my $wordNumber;
my $horizMask;
my $vertMask;
my $horizInsertedWord; #for quick removal on failed recursions
my $vertInsertedWord; #for quick removal on failed recursions

%letterBackTrackSource = (); #clear global indicating that we are moving forward and have cleared the backtrack state

if (scalar @nextLetterPositionsOnBoard == 0) {return 1}; #if we have filled all the possible letters, we are done. This breaks us out of all recursive  success loops

my %cellPosition =  %{ shift @nextLetterPositionsOnBoard }; #keep %cellPosition in subroutine unchaged as we may need to unshift on a recursive return
my $x = $cellPosition{x};
my $y = $cellPosition{y};

if ($in{shuffle}) {
     @lettersThatFit =  shuffle &lettersPossibleAtCell($x,$y); # 0.000059 sec per call
     }
else {
      @lettersThatFit = sort {$b cmp $a} &lettersPossibleAtCell($x,$y); # 0.000059 sec per call
      }

$recursiveCount++; #count forward moving calls

if ($debug) {print "we are moving forward and working on pos $x $y , letters that fit: @lettersThatFit  \n"};

my $success = 0;
while ($success == 0)
        {
        if (scalar @lettersThatFit == 0) #are there any possible words? If no backtrack
              {
              #fail to find a list of letters going forward or we are out of letters in a recursion so go back a letter
              #&SetXY($x,$y,$unoccupied);
              unshift @nextLetterPositionsOnBoard , {x => $x, y => $y}; #always unshift our current position back on to @nextLetterPositionsOnBoard when we return!

              #optimal backtrack option. saves hundreds of naive backtracks!
              #get/set global touchingLetters and backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!
              if ($in{optimalbacktrack} == 1) {
                   if (%letterBackTrackSource == ()) { #ignore setting backtrack if we are already backtracking
                        if ( $targetLettersForBackTrack{$x}{$y} != undef ) { #check to see if there are any backtrack targets possible for $x $y first
                              #&GetTouchingLetters($x,$y);
                              $letterBackTrackSource{'x'} = $x;
                              $letterBackTrackSource{'y'} = $y;
                              if ($debug) {print "optimum set \%letterBackTrackSource  $letterBackTrackSource{x} $letterBackTrackSource{y}\n"}
                              }
                        }
                  }
              if ($debug) {print "out of letters at $x,$y  \n"}
              return 0;
              }; #no letters so fail

        #try the next word that fit in this location
        $popLetter = pop @lettersThatFit;
        &SetXY($x,$y,$popLetter); #lay letter so we can test masks below
        if ($debug) {print "laying $popLetter at $x,$y\n"}

        #see if horizontal and vertical word is already selected. If so, fail + backtrack
        #horiz
        $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
        if ($wordNumber > 0) {
             $horizMask = $allMasksOnBoard[$wordNumber][0];
             if ( &IsWordAlreadyUsed($horizMask) ) { #this word is already used. fail
                   &SetXY($x,$y,$unoccupied);
                   if ($debug) {print "horiz mask exists at $x,$y\n"}
                   next ; #choose another word ie. pop
                   }
             }
        #vert
        $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
        if ($wordNumber > 0) {
             $vertMask = $allMasksOnBoard[$wordNumber][1];
             if ( &IsWordAlreadyUsed($vertMask) ) { #this word is already used. fail
                   &SetXY($x,$y,$unoccupied);
                   if ($debug) {print "vert mask exists at $x,$y\n"}
                   next ; #choose another word ie. pop
                   }
             }

        #continue and mark horiz and vert words if full words

        #check to see if horiz and vert mask are full words. if so then mark word as used
        #how will we unmark?
        #horiz
        if ($horizMask != ()) { #is there a horiz mask?
             if (not $horizMask =~ /$unoccupied/) {
                 if ($wordsThatAreInserted{$horizMask} == 0) {#word not used set as used
                      $horizInsertedWord = $horizMask; #so we can easily remove on failed recursions
                      $wordsThatAreInserted{$horizMask} = 1;
                      }
                 else { #this word is already used. fail
                         &SetXY($x,$y,$unoccupied);
                         if ($debug) {print "horiz word exists at $x,$y\n"}
                         next ; #choose another word ie. pop
                         }
                 }
            }
        #vert
        if ($vertMask != ()) { #is there a vert mask?
             if (not $vertMask =~ /$unoccupied/) {  #word not used set as used
                 if ($wordsThatAreInserted{$vertMask} == 0) { #this word is already used. fail
                      $vertInsertedWord = $vertMask; #so we can easily remove on failed recursions
                      $wordsThatAreInserted{$vertMask} = 1;
                      }
                 else { #this word is already used. fail
                         &SetXY($x,$y,$unoccupied);
                         if ($debug) {print "vert word exists at $x,$y\n"}
                         next ; #choose another word ie. pop
                         }
                 }
             }

        if (time() > $oldTime + 2) #print every 3 seconds
              {
              if ($debug) {print time()-$timeForCrossword . " sec wordNumber:$wordNumber , dir:$dir $popLetter optimalBacktrack:$optimalBacktrack naiveBacktrack:$naiveBacktrack recursive calls:$recursiveCount\n";}
              else {print '.';} # otherwise apache timeout directive limit is reached
              #print '.';
              &PrintProcessing();
              $oldTime = time();
              }

        #attempt to lay next letter
        $success = &RecursiveLetters(); #lay next letter in the next position
        if ($success == 1){return 1;}; #board is filled, return out of all recursive calls successfuly
#---------------
        #if we are here, the last recursive attempt to lay a word failed. So we are backtracking.
        #returning from last letter which failed

         #maybe undef $wordsThatAreInserted{$horizInsertedWord} for speed
         delete $wordsThatAreInserted{$horizInsertedWord};  #allow us to reuse word
         delete $wordsThatAreInserted{$vertInsertedWord};  #allow us to reuse word

        #failed so reset letter to unoccupied
        &SetXY($x,$y,$unoccupied);

        if ($in{optimalbacktrack} == 0)
             {
             %letterBackTrackSource = (); #stop optimal recursion?
             }

        if ($debug) {print "letterbacktrack source: x:$letterBackTrackSource{x} y:$letterBackTrackSource{y}\n"};
        #optimal backtrack check and processing
        if (%letterBackTrackSource != ())
             {
              #we are doing an optimal backtrack
              #if ($targetLettersForBackTrack{$x}{$y} == 1) {
              if ($debug) {print "\$targetLettersForBackTrack{$letterBackTrackSource{x}}{$letterBackTrackSource{y}}{$x}{$y} = $targetLettersForBackTrack{$letterBackTrackSource{x}}{$letterBackTrackSource{y}}{$x}{$y}\n"}
              #note that set to > 0 (no shadows as british style (odd not even) does not work with > 1 (shadows)
              if ($targetLettersForBackTrack{$letterBackTrackSource{'x'}}{$letterBackTrackSource{'y'}}{$x}{$y} > 0) { #if it is equal to one, it is in a 'shaddow' and does not affect the failed letter
                   #we have hit the optimal target. turn off optimal backtrack
                   #%targetLettersForBackTrack = ();
                   if ($debug) {print "wipe \%letterBackTrackSource\n"}
                   %letterBackTrackSource = ();
                   }
              else {
                    #still in optimal backtrack so keep going back
                    unshift @nextLetterPositionsOnBoard , {x => $x, y => $y}; #always unshift our current position back on to @nextLetterPositionsOnBoard when we return!
                    $optimalBacktrack++;
                    if ($debug) {print "optimum skip at $x,$y\n"}
                    return 0;
                    }
              }
        if ($debug) {print "landed at $x,$y\n\n"}
        $naiveBacktrack++;
        next; #naive backtrack
        }

die('never get here'); #never get here
}

sub GetCrossingWords()
{
#input: word number and direcction
#output: [[$crossingWordNumber,$crossingWordDir],[$crossingWordNumber,$crossingWordDir],[$crossingWordNumber,$crossingWordDir],...]

my @crossingWords;
my $wordNumber = $_[0];
my $dir = $_[1];

my $x;
my $y;
my $crossingWordDir;
my $letterPosition;
my $crossingWordNumber;

my @wordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]};
foreach $letterPosition (@wordLetterPositions)
  {
  $x = $letterPosition->[0];
  $y = $letterPosition->[1];
  $crossingWordDir =  $OppositeDirection[$dir];

  #find and mark crossing words
  $crossingWordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$crossingWordDir];
  if ( $crossingWordNumber > 0 )
        {
        push @crossingWords , [$crossingWordNumber,$crossingWordDir];
        }
    }
return @crossingWords;
}

sub WordsFromLetterLists()
{
#input list of referenced lists containing possible letters for each position in a word
#(['C','D','F','T','Z'] , ['E','R','T','Y','O', 'A'] , ['T','R','E','W','Q','Z'])
#(['C','D','F','T','Z'] , [$padsEitherSide] , ['T','R','E','W','Q','Z'])
#if input is () no letters were available from LetterListFor so return ()
#if a letter position has no potential letters (it == ()) return () unless it has a pad on either side!
#$padsEitherSide note in this case, there will be no letters returned, BUT words still can be made as there is no crossing word to block it. So we assume all letters are possible here [A-Z]
#output list of words that can be made with said letters

my @letterLists = @_;
my $wordLength = scalar @letterLists;
my $adjustableWordLength = $wordLength; #used to compare our hash containing how many times a word was found and how many letters were used to find them
my $letterPosition = -1; #start at -1 as we increment at top of loop!
my @nThLetterWordList;
my @possibleWords;
my @runningWordList;
my @wordsFromLetters;
my @letterList;
my %possibleWordsCount;
my $localWord;

if (scalar @letterLists == 0) {return()}; #required as LetterListsFor will return () if there are no possible letters!

#regex version fronm 2x  up to 20x faster! long lists are fast
my $regexpstring = '';
foreach my $referenceLetterList (@letterLists) #for each letter's position
        {
        @letterList = @{$referenceLetterList};
        #if (scalar @letterList == 0) { return (); } #no possible letters here, return an empty list of words
        if ($letterList[0] eq $padsEitherSide) {@letterList = ('A'..'Z')} #replace $padsEitherSide with (A..Z)
        else { if (scalar @letterList == 0) { return (); } }#no possible letters here, return an empty list of words
        $regexpstring = $regexpstring . '[' . join('' , @letterList) . ']';
        }

# ($wordsOfLengthString[$wordLength] =~ /$regexpstring/g) returns all possible words
#look for words already used and ignore using map!
#@possibleWords = map( { if ( $wordsThatAreInserted{$_} == 0 ) {$_} else {()} }   ($wordsOfLengthString[$wordLength] =~ /$regexpstring/g) );
#return @possibleWords; # speed up by direct output!
return map( { if ( $wordsThatAreInserted{$_} == 0 ) {$_} else {()} }   ($wordsOfLengthString[$wordLength] =~ /$regexpstring/g) );
}

sub LetterListsFor()
{
#input: word number and direcction
#output: list of possible letters for each position in word based on crossing word masks
#if a letter position has no members so what. keep going but make sure that the list for that letter = ()

my $wordNumber = $_[0];
my $dir = $_[1];

my $wordLength = length($allMasksOnBoard[$wordNumber][$dir]);
my @wordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]};
my @letterLists;
my @nThLetters;

foreach my $letterPosition (@wordLetterPositions)
  {
  my $x = $letterPosition->[0];
  my $y = $letterPosition->[1];
  my $crossingWordDir =  $OppositeDirection[$dir];

  my $crossingWordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$crossingWordDir];
  my $crossingWordMask = $allMasksOnBoard[$crossingWordNumber][$crossingWordDir];

  my $nThLetterPosition = $PositionInWord[$x][$y][$crossingWordDir];
  my $crossingLetter = substr($crossingWordMask , $nThLetterPosition , 1);

  @nThLetters = ();
  if ($crossingLetter =~ /[A-Z]/ ) { #if a letter is already in the crossing spot, use it.
       @nThLetters = ($crossingLetter)
       }
  if ($crossingLetter =~ /$unoccupied/ )
       {
       my @wordsFromMask = &WordsFromMask($crossingWordMask);
       @nThLetters = &NthLettersFromListOfWords($nThLetterPosition , [@wordsFromMask]);
       }
  if ($crossingWordNumber == undef) { #there is no crossing word at this letter location so return a single $unoccupied 'o' to indicate that a word can still be made as any letter can go here!
       #@nThLetters = ($unoccupied);
       @nThLetters = ($padsEitherSide);
       }
  if ( scalar @nThLetters == 0) #used to break out earier for small speed increase. If a letter position has no letters, WordsFromLetterList will fail anyway. Just return empty list
        {
        @letterLists = ( () );
        last;
        }
  push @letterLists , [@nThLetters];
  }
return @letterLists;
}

sub NthLettersFromListOfWords() #tested
{
#input:
# number representing position in words
# reference to list of words all the same length
#output a list of all letters at the requested position from each word (no duplicates!)

my $nth = $_[0];
my @words = @{$_[1]};
my $word;
my %letters = ();
my $letter;
my $count;

foreach $word (@words)
         {
         if (length($word) <= $nth ) {die("@words $count word $word of length  too short nth $nth")}
         $letter = substr($word , $nth , 1); #substr is 0 based
         $letters{$letter} = 1;
         }
return keys %letters;
}

sub LettersFromMaskAndPos
{
#start with letter pos (0 based)
#mask letters should be capatalized
#input: A_PL_ where _ will be whatever $unoccupied is
#output list of letters that match the input mask (test for $wordsThatAreInserted)

my $mask = $_[0];
my $letterPosition = $_[1];
my %letterList; # hash keys used to avoid duplicates!
my $wordLength = length($mask);

$mask =~ s/$unoccupied/\./g; #make a mask of 'GO$unoccupiedT' into 'GO.T' for the regexp

#need to fileter out $wordsThatAreInserted{$popWord} == 1 below if ( $wordsThatAreInserted{$popWord} == 1 )
#substr is 0 based
%letterList = map(
              {
              if ( $wordsThatAreInserted{$_} == 0 ) { substr($_ , $letterPosition , 1)  =>  1 }
              else {()} #required or somehow a 1 will get into the letter list
              }
   ($wordsOfLengthString[$wordLength] =~ /($mask),/g) ); #returns a list of found words in the string!
# %hash = map { get_a_key_for($_) => $_ } @array;
return keys %letterList;
}

sub WordsFromMask
{#mask letters should be capatalized
#input: A_PL_ where _ will be whatever $unoccupied is
#output list of words that match the input mask

my $mask = $_[0];

my @word_list;
my $wordLength = length($mask);

$mask =~ s/$unoccupied/\./g; #make a mask of 'GO$unoccupiedT' into 'GO.T' for the regexp

#need to fileter out $wordsThatAreInserted{$popWord} == 1 below if ( $wordsThatAreInserted{$popWord} == 1 )
#note that we need to return an empty list if the word is already inserted see:  else {()} If we do not, the map will return an empty word in the middle of the list which will pooch our code later.
return map( { if ( $wordsThatAreInserted{$_} == 0 ) {$_} else {()} }  ($wordsOfLengthString[$wordLength] =~ /($mask),/g) ); #returns a list of found words in the string!
#@word_list = map( { if ( $wordsThatAreInserted{$_} == 0 ) {$_} else {()} }  ($wordsOfLengthString[$wordLength] =~ /($mask),/g) ); #returns a list of found words in the string!
#return @word_list;
}

sub placeMaskOnBoard()
{
#place word AND add letters to all the associated crossing words!
my $wordNumber = $_[0];
my $wordDir = $_[1];
my $word = $_[2];

if ($word eq '') {die("no word. wordnumber:$wordNumber worddir:$wordDir ")};
#print "$word\n\n";
my $wordLetterPosition = -1;
foreach my $letterPosition (@{$letterPositionsOfWord[$wordNumber][$wordDir]})
        {
        my $x = $letterPosition->[0];
        my $y = $letterPosition->[1];
        $wordLetterPosition++;

        my $letter = substr($word , $wordLetterPosition , 1); #letter from word
        SetXY($x,$y,$letter);
        }
return;
}

sub SetXY()
{
#only for fill letter routines. not fill word
my $x = $_[0];
my $y = $_[1];
my $letter = $_[2];
my $wordNumber;
my $position;

$puzzle[$x][$y]->{Letter} = $letter; #keep grid up to date!

#set horiz mask
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
$position = $PositionInWord[$x][$y][0];
if ($wordNumber != undef)
     {
     #print ("horiz mask x:$x y:$y wordNumber:$wordNumber horiz:$allMasksOnBoard[$wordNumber][0] vert:$allMasksOnBoard[$wordNumber][1] position:$position letter:$letter\n\n");
     #place letter in $allMasksOnBoard
     #this can be moved to a highr level and done directly if we ONLY lay down whole words
     substr($allMasksOnBoard[$wordNumber][0] , $position , 1 , $letter) or die ("horiz mask x:$x y:$y wordNumber:$wordNumber horiz:$allMasksOnBoard[$wordNumber][0] vert:$allMasksOnBoard[$wordNumber][1] position:$position letter:$letter");
     }

#set vert mask
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
$position = $PositionInWord[$x][$y][1];
if ($wordNumber != undef)
     {
     #print ("vert mask x:$x y:$y wordNumber:$wordNumber horiz:$allMasksOnBoard[$wordNumber][0] vert:$allMasksOnBoard[$wordNumber][1] position:$position letter:$letter\n\n");
     #PrintProcessing;
     substr($allMasksOnBoard[$wordNumber][1] , $position , 1 , $letter) or die ("vert mask x:$x y:$y wordNumber:$wordNumber horiz:$allMasksOnBoard[$wordNumber][0] vert:$allMasksOnBoard[$wordNumber][1] position:$position letter:$letter");
     }
}

sub GetXY()
{
my $x = $_[0];
my $y = $_[1];
my $letter;
my $wordNumber;
my $word;
my $position;
my $dir;

return $puzzle[$x][$y]->{Letter};
}

sub javascriptArrayFromLetterPositions()
{
#input array from @LetterPositions [[x,y][][]]
#output x,y,x,y,x,y...
my @wordLetterPositions;
my $positionPair;

foreach $positionPair (@_) #get all letter pos
         {
         push @wordLetterPositions , (${$positionPair}[0] , ${$positionPair}[1]);
         }
my $er =  join(',' , @wordLetterPositions); #make a string version for javascript
return "$er";
}

sub print_puzzle {
my @temppuzzle;
my ($a,$temp,$temp2,$temp3,$temp4,$temp5);
my $y;
my $x;
my $word;
my $wordNumber;
my ($dir , $direction);
my $wordLetterPositions;

$temp = "<table cellspacing='0' cellpadding='0' CLASS='tableclass'>";
for ($y = 0; $y < $in{height}; $y++)
        {
        $temp .= "<tr>";
                for ($x = 0; $x < $in{width}; $x++)
                      {
                      $temp3 = '';
                      $temppuzzle[$x][$y]->{Letter} = $puzzle[$x][$y]->{Letter}; #mimic filled in puzzle
                      for ($dir = 0 ; $dir < 2 ; $dir++)
                            {
                            #if ( ($PositionInWord[$x][$y][$dir] == 0) and ($PositionInWord[$x][$y][$dir] ne undef) ) #we are at start of word so there will be a number here
                            #if ($PositionInWord[$x][$y][$dir] eq 0)  #we are at start of word so there will be a number here
                            if ( not defined $PositionInWord[$x][$y][$dir] ) {next;}
                            if ($PositionInWord[$x][$y][$dir] == 0)  #we are at start of word so there will be a number here
                                 {
                                 $temppuzzle[$x][$y]->{Letter} = $ThisSquareBelongsToWordNumber[$x][$y][$dir];
                                 #print"startofword $ThisSquareBelongsToWordNumber[$x][$y][$dir] x:$x y:$y dir:$dir\n";
                                 }

                            #build a hover clue text for each square
                            $word = $allMasksOnBoard[$ThisSquareBelongsToWordNumber[$x][$y][$dir]][$dir];
                            if ($word ne undef)
                                 {
                                 if ($dir == 0) {$direction = 'Across'}
                                 if ($dir == 1) {$direction = 'Down'}
                                 $temp3 .= "$direction: $clues{$word} \n";
                                 $temp3 =~ s/[\'\"]//g; #remove quotes from title s it is in a tag
                                 }
                            }

                      $temp4 = ""; #clear the soon to be choose() routine variable
                      my $wordcount = 0;
                      if ($ThisSquareBelongsToWordNumber[$x][$y][0] ne undef) {$wordcount++} #horiz word here
                      if ($ThisSquareBelongsToWordNumber[$x][$y][1] ne undef) {$wordcount++} #vert word here
                      if ($wordcount == 2) #horiz and vert word here
                          {
                          $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
                          $word = $allMasksOnBoard[$wordNumber][0];
                          $wordLetterPositions = &javascriptArrayFromLetterPositions(@{$letterPositionsOfWord[$wordNumber][0]});
                          $temp4 .= qq|if (horizvert == 0) {choose("$word" , $x , $y , [$wordLetterPositions])};|;
                          $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
                          $word = $allMasksOnBoard[$wordNumber][1];
                          $wordLetterPositions = &javascriptArrayFromLetterPositions(@{$letterPositionsOfWord[$wordNumber][1]});
                          $temp4 .= qq|if (horizvert == 1) {choose("$word" , $x , $y , [$wordLetterPositions])};|;
                          }
                      if ($wordcount == 1) #horiz word here
                          {#just choose the one word
                          if ($ThisSquareBelongsToWordNumber[$x][$y][0] ne undef)
                               {
                               $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
                               $word = $allMasksOnBoard[$wordNumber][0];
                               $wordLetterPositions = &javascriptArrayFromLetterPositions(@{$letterPositionsOfWord[$wordNumber][0]});
                               $temp4 = qq|choose("$word" , $x , $y , [$wordLetterPositions]);|;
                               }
                          if ($ThisSquareBelongsToWordNumber[$x][$y][1] ne undef)
                               {
                               $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
                               $word = $allMasksOnBoard[$wordNumber][1];
                               $wordLetterPositions = &javascriptArrayFromLetterPositions(@{$letterPositionsOfWord[$wordNumber][1]});
                               $temp4 = qq|choose("$word" , $x , $y , [$wordLetterPositions]);|;
                               }
                          }
                      $temp4 .= qq|ToggleHV();|;

                      #$temp5 = 'document.getElementById(CurrentFocus).innerHTML=String.fromCharCode(event.keyCode||event.which);HighlightNextBox();';
                      #$temp5 = 'document.getElementById(CurrentFocus).innerHTML=String.fromCharCode(event.which);HighlightNextBox();';
                      #$temp5 = 'document.getElementById("cell_$x\_$y").innerHTML=String.fromCharCode(event.which);HighlightNextBox();';
                      #$temp5 = qq|document.getElementById(cell_$x\_$y).innerHTML=String.fromCharCode(event.keyCode\|\|event.which);HighlightNextBox();|;
                      #$temp5 = qq|this.innerHTML=String.fromCharCode(event.keyCode\|\|event.which);HighlightNextBox();|;

                      #lay down table stuff here

                      #black square
                      if ($puzzle[$x][$y]->{Letter} eq $padChar) #make sure our page width is fixed
                             {$temp .= "<td CLASS='tdblackclass'><spacer width='20 pt'></td>";}

                      #number square
                      if ($temppuzzle[$x][$y]->{Letter} =~ /[0-9]/)
                            {
                            $temp .= qq|
                            <TD VALIGN='TOP' ALIGN='LEFT' CLASS='tdnumberclass'>
                            <DIV  style='position: absolute; z-index: 2;'>$temppuzzle[$x][$y]->{Letter}</DIV>
                            <TABLE CELLPADDING="0" CELLSPACING="0">
                                  <TBODY>
                                         <TR>
                                                <TD title='$temp3' CLASS='tdwhiteclass' ID='cell_$x\_$y'
                                                ONCLICK='$temp4' VALIGN='middle' WIDTH='20' ALIGN='center'
                                                HEIGHT='25'>&nbsp;</TD>
                                         </TR>
                                  </TBODY>
                                </TABLE>
                            </TD>
                            |;
                            }

                      #unoccupied square
                      #if ($temppuzzle[$x][$y]->{Letter} =~ /[A-Z,o]/)
                      if ($temppuzzle[$x][$y]->{Letter} =~ /[A-Z]/)
                            {
                            $temp .= qq| <td title='$temp3' ID='cell_$x\_$y' CLASS='tdwhiteclass' ONCLICK='$temp4'>&nbsp;</td>|;
                            }
                      }
        $temp .= "</tr>\n";
        }

$temp .= "</table>\n";
return $temp;
};

sub print_solved_puzzle {
my $temp;
my $y;
my $x;

$temp = "<table cellspacing='0' CLASS='tableclass'>";
for ($y = 0; $y < $in{height}; $y++)
        {
        $temp .= "<tr>";
                for ($x = 0; $x < $in{width}; $x++)
                      {
                      if ($puzzle[$x][$y]->{Letter} eq $padChar)
                             {$temp .= "<td CLASS='tdblackclass'></td>";next;}
                      if ($puzzle[$x][$y]->{Letter} eq $unoccupied)
                             #{$temp .= "<td CLASS='tdblackclass'></td>";next;}
                             #{$temp .= "<td CLASS='tdwhiteclass'>$puzzle[$x][$y]->{Letter}</td>"}
                             {$temp .= "<td CLASS='tdwhiteclass'>&nbsp</td>"}
                      #if ($puzzle[$x][$y]->{Letter} =~ /[a-zA-Z$unoccupied]/)
                      if ($puzzle[$x][$y]->{Letter} =~ /[A-Z1-9]/)
                            {$temp .= "<td CLASS='tdwhiteclass'>$puzzle[$x][$y]->{Letter}</td>"}
                      }
        $temp .= "</tr>\n";
        }
$temp .= "</table>\n";
return $temp;
}

sub LetterPositionsOfWord()
{
#input x , y word start pos and direction and word length
#output an array of x,y pos of all letters in the word
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $wordLength = $_[3];
my @arrayOfLetterPositions;

for ($a = 0 ; $a < $wordLength ; $a++)
      {
      push @arrayOfLetterPositions , [$x + (($OppositeDirection[$dir]) * $a) , $y + ($dir * $a)];
      }
return  @arrayOfLetterPositions;
}

sub outsideCrossword {
my $x = $_[0];
my $y = $_[1];
if ( ($x >= $in{width} ) || ($y >= $in{height} ) ) {return 1}
if ( ($x < 0) || ($y < 0) ) {return 1}
return 0;
};

sub calcWordSize ()
{
#input x , y pos and direction. Note it might be in middle of word
#output the size of word that will fit from start of word to the next pad char or the edge or xword. based on the @puzzle grid
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $count;

if ( &outsideCrossword($x,$y) ) {return 0;}
if ($puzzle[$x][$y]->{Letter} eq $padChar) {return 0} #no word length possible on a pad

($x,$y) = &findStartOfWord($x,$y,$dir);
# count forward until pad char (last possible word letter)
until ( ($puzzle[$x][$y]->{Letter} =~ /$padChar/) or &outsideCrossword($x,$y) )
         {
         $x = $x + ($OppositeDirection[$dir]);
         $y = $y + $dir;
         $count++;
         }
return $count;
}

sub findStartOfWord()
{
#input x , y pos and direction
#output the x , y position of the start of word based on the @puzzle grid
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $count;

#back up to location of start of word
#until ( ($puzzle[$x][$y]->{Letter} =~ /$padChar/) or ($puzzle[$x][$y]->{Letter} =~ /$padCharTemp/) or &outsideCrossword($x,$y) )
until ( ($puzzle[$x][$y]->{Letter} =~ /$padChar/) or &outsideCrossword($x,$y) )
         {
         $x = $x - ($OppositeDirection[$dir]);
         $y = $y - $dir;
         }
#get back to start of word as we have gone too far!
$x = $x + ($OppositeDirection[$dir]);
$y = $y + $dir;
return ($x, $y);
}

sub blankMaskOnBoard()
{
my $wordNumber = $_[0];
my $wordDir = $_[1];
my $mask = $allMasksOnBoard[$wordNumber][$wordDir];

$mask =~ s/./$unoccupied/g; # fill mask with $unoccupied
&placeMaskOnBoard($wordNumber , $wordDir , $mask);
}

sub Insert()
{
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $word = $_[3];
my $temp;
my $temp2;
my @temp;
my $temp3;
my $Ignore_Crosses;

if ($word eq '')
     {
     return($x , $y , $dir , '')
     } #no word can fit at this location

@temp = split(// , $word); #split word into letters

$x = $_[0];
$y = $_[1];

#pad at start of word to avoid word butting

#if (scalar(@temp) > 0) {$puzzle[$x - (not $dir)][$y - $dir]->{Letter} = $padChar};
if ( $dir == 0 and ($x != 0) ) {$puzzle[$x - (not $dir)][$y - $dir]->{Letter} = $padChar};
if ( $dir == 1 and ($y != 0) ) {$puzzle[$x - (not $dir)][$y - $dir]->{Letter} = $padChar};

$temp2 = 0;
foreach $temp (@temp) #for each letter in the word
         {
         $puzzle[$x][$y]->{Letter} = $temp; #add letter to grid

         $x = $x + (not $dir);
         $y = $y + $dir;
         $temp2 = $temp2 + 1;
         }
#pad at end of word to avoid word butting
if ( $dir == 0 and ($x < $in{width}) ) {$puzzle[$x][$y]->{Letter} = $padChar};
if ( $dir == 1 and ($y < $in{height}) ) {$puzzle[$x][$y]->{Letter} = $padChar};

return ($_[0] , $_[1] , $dir , $word); # let other routines know what we have done
};

sub parse_form {
# --------------------------------------------------------
# Parses the form input and returns a hash with all the name
# value pairs. Removes SSI and any field with "---" as a value
# (as this denotes an empty SELECT field.

        my (@pairs, %in);
        my ($buffer, $pair, $name, $value);

        if ($ENV{'REQUEST_METHOD'} eq 'GET') {
                @pairs = split(/&/, $ENV{'QUERY_STRING'});
        }
        elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
                read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
                 @pairs = split(/&/, $buffer);
        }
        else {
                &cgierr ("This script must be called from the Web\nusing either GET or POST requests\n\n");
        }
        PAIR: foreach $pair (@pairs) {
                ($name, $value) = split(/=/, $pair);

                $name =~ tr/+/ /;
                $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

                $value =~ tr/+/ /;
                $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

                $value =~ s/<!--(.|\n)*-->//g;                          # Remove SSI.
                if ($value eq "---") { next PAIR; }                  # This is used as a default choice for select lists and is ignored.
                (exists $in{$name}) ?
                        ($in{$name} .= "~~$value") :              # If we have multiple select, then we tack on
                        ($in{$name}  = $value);                                  # using the ~~ as a seperator.
        }
        return %in;
}

    sub lock {
        my ($fh) = @_;
        flock($fh, LOCK_EX) or print "Cannot lock file - $!\n";
        # and, in case someone appended while we were waiting...
        #seek($fh, 0, SEEK_END) or die "Cannot seek - $!\n";
    }
    sub unlock {
        my ($fh) = @_;
        flock($fh, LOCK_UN) or print "Cannot unlock file - $! $_[0]\n";
    }

sub cgierr
{
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.

if ($debug == 0) {
     print "Epic fail....";
     &Quit();
     }

print "<PRE>\n\nCGI ERROR\n==========================================\n";
$_[0]      and print "Error Message       : $_[0]\n";
$0         and print "Script Location     : $0\n";
$]         and print "Perl Version        : $]\n";

    print "\nForm Variables\n-------------------------------------------\n";
    foreach my $key (sort keys %in)
            {
            my $space = " " x (20 - length($key));
            print "$key$space: $in{$key}\n";
            }

    print "\nEnvironment Variables\n-------------------------------------------\n";
    foreach my $env (sort keys %ENV)
            {
            my $space = " " x (20 - length($env));
            print "$env$space: $ENV{$env}\n";
            }
print "\n</PRE>";

&Quit();
exit -1;
};

sub GenerateNextLetterPositionsOnBoardFlat
{
#create right to left top to bottom list in which we will lay down words. FIFO
my $x = 0;
my $y = 0;

@nextLetterPositionsOnBoard = ();
for ($y = 0 ; $y < $in{height} ; $y++)
     {
     for ($x = 0 ; $x < $in{width} ; $x++)
             {
             if ($puzzle[$x][$y]->{Letter} ne $padChar)
                  {
                  push @nextLetterPositionsOnBoard , {x => $x , y => $y};
                  if ($debug) {print "($x,$y)"}
                  }
             }
         }
}

sub GenerateNextLetterPositionsOnBoardZigZag
{
#create a top right to bottom left list in which we will lay down words. FIFO
#zigzag alternate top right to bottom left then botom left to top right
my $x = 1;
my $y = -1;
my $divX = -1;
my $divY = 1;

@nextLetterPositionsOnBoard = ();
do {
        #move cursor
        $x = $x + $divX;
        $y = $y + $divY;
        #test cursor position
        if ( ($x < 0) and ($y >= $in{height}) ) {#bottom left corner
               $divX = -$divX; $divY = -$divY; #change directions
               $x = 1;
               $y = $in{height} - 1;
               }
        if ( ($x >= $in{width}) and ($y < 0) ) {#top right corner
               $divX = -$divX; $divY = -$divY; #change directions
               $x = $in{width} - 1;
               $y = 1;
               #$myWidth = $in{width};
               }
        if ($x < 0){#off left
             $divX = -$divX; $divY = -$divY; #change directions
             $x = 0;
             }
        if ($y < 0){#off top
             $divX = -$divX; $divY = -$divY; #change directions
             $y = 0;
             }
        if ($x >=  $in{width}){#off right
             $divX = -$divX; $divY = -$divY; #change directions
             $x =  $in{width} - 1;
             $y = $y + 2;
             }
        if ($y >=  $in{height}){#off bottom
             $divX = -$divX; $divY = -$divY; #change directions
             $x =  $x + 2;
             $y = $in{height} - 1;
             }
        if ($debug) {print "($x,$y)"}
        #process cursor position
        if ($puzzle[$x][$y]->{Letter} ne $padChar)
                  {
                  push @nextLetterPositionsOnBoard , {x => $x, y => $y};
                  }
        }
until ( ($x == $in{width} - 1) and ($y == $in{height} - 1) );
}

sub GenerateNextLetterPositionsOnBoardDiag
{
#create a top right to bottom left list in which we will lay down words. FIFO
#better than zig zag
my $x = 1;
my $y = -1;
my $divX = -1;
my $divY = 1;
my $diagCount;

@nextLetterPositionsOnBoard = ();

do {
    #move cursor
    $x = $x + $divX;
    $y = $y + $divY;

    if (($x < 0) or ($y >= $in{height}) ) {
          $diagCount++;
          $x = $diagCount;
          if ($x >= $in{width} - 1) {
               $x = $in{width} - 1;
               $y = $diagCount - $x;
               }
          else {
                $y = 0;
                }
          }
    if ($debug) {print "($x,$y)"}
    #process cursor position
    if ($puzzle[$x][$y]->{Letter} ne $padChar) {
         push @nextLetterPositionsOnBoard , {x => $x, y => $y};
         }
    }
until ( ($x >= $in{width} - 1) and ($y >= $in{height} - 1) );
}

sub GenerateNextLetterPositionsOnBoardSwitchWalk
{
#create a top right to bottom left list in which we will lay down words. FIFO
my $x = 0;
my $y = 0;
my $xx = 0; #last starting run
my $yy = 0; #last starting run
my $dir = 0; #horiz first

@nextLetterPositionsOnBoard = ();

do
        {
        if ($puzzle[$x][$y]->{Letter} ne $padChar)
                  {
                  push @nextLetterPositionsOnBoard , {x => $x, y => $y};
                  }
        if ($x == $in{width}-1)
             {
             $x = $xx ;
             $y = $yy ;
             $yy = $yy + 1;
             $dir = 1;
             }
        if ($y == $in{height}-1)
             {
             $x = $xx;
             $y = $yy ;
             $xx = $xx + 1;
             $dir = 0;
             }
        $x = $x + (not $dir);
        $y = $y + $dir;
        }
until (($x + $y + 2) > ($in{height}+$in{width}));
}

sub GenerateNextLetterPositionsOnBoardSnakeWalk
{
#create a top right to bottom left list in which we will lay down words. FIFO
my $dir;
my $walkLength = 0;
my $walkStep;
my $x;
my $y;

@nextLetterPositionsOnBoard = ();

if ($in{height} != $in{width}) {
     die("The grid is not square. snake walk failed.");
     }

do {
    $walkLength++;
    for ($dir = 0 ; $dir < 2 ; $dir++) {
          if ($dir == 0) {
               $y = $walkLength - 1;
               $x = 0;
               }
          else {
                $y = 0;
                $x = $walkLength;
                if ( $walkLength == ($in{height}) ) {next} #skip lat one
                }
          for ($walkStep = 1 ; $walkStep <= $walkLength ; $walkStep++) {
                if ($puzzle[$x][$y]->{Letter} ne $padChar) {
                     if ($debug) {print "dir:$dir walkStep:$walkStep walkLength:$walkLength ($x,$y)\n"}
                     push @nextLetterPositionsOnBoard , {x => $x, y => $y};
                     }
                $x = $x + (not $dir);
                $y = $y + $dir;
                }
          }
    }
until ($walkLength > $in{height} - 1);

}

sub lettersPossibleAtCell()
{
#at the input position x,y and given the prefix of a word for a mask, find and return all possible letters
my $x = $_[0];
my $y = $_[1];
my @lettersThatFit;
my $wordNumber;
my @lettersVert;
my @lettersHoriz;
my $mask;
my $isVertWord;
my $isHorizWord;

#find vert mask and possible letters
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
if ($wordNumber > 0) { #there is a vert mask
     $isVertWord = 1;
     $mask = $allMasksOnBoard[$wordNumber][1]; # get WORD or MASK at this crossword position
     @lettersVert = keys %{$linearWordSearch{$mask}};
     if (scalar @lettersVert == 0 ) { #should never get here as our $linearWordSearch does not stop mid word
           die ('no \@lettersVert. impossible');
           }
     }

#find horiz mask and possible letters
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
if ($wordNumber > 0) { #there is a horiz mask
     $isHorizWord = 1;
     $mask = $allMasksOnBoard[$wordNumber][0]; # get WORD or MASK at this crossword position
     @lettersHoriz = keys %{$linearWordSearch{$mask}};
     if ( scalar @lettersHoriz == 0 ) { #should never get here as our $linearWordSearch does not stop mid word
            die ('no \@lettersHoriz. impossible');
           }
     }

if (($isHorizWord) and ($isVertWord)) { #there is a horiz and vert word at this cell. find inersection of possible letters
     @lettersThatFit = intersection(\@lettersHoriz , \@lettersVert);
     if ($debug) {print "Horiz and Vert letters @lettersThatFit found at $x $y\n"}
     return @lettersThatFit;
     }
if ((not $isHorizWord) and ($isVertWord)) { #there is only a vertical word at this cell
     if ($debug) {print "Vert letters @lettersVert found at $x $y\n"}
     return @lettersVert;
     }
if (($isHorizWord) and (not $isVertWord)) { #there is only a horizontal word at this cell
      if ($debug) {print "Horiz letters @lettersHoriz found at $x $y\n"}
     return @lettersHoriz;
     }
die('should not get to end of letterPossibleAt()');
};

sub IsWordAlreadyUsed() {
#input of mask WORooooo
#check to see if all possible letters 'o' are singles. If so word is unique. then see if word has been used
#saves us from filling in a whole word on letter fills only to have to backtrack
my $mask = $_[0];
my @nextLetters;

while ($mask =~ /o/g) { #see if we get single letters until end of word
        @nextLetters = &getNextPossibleLetters($mask);
        if (scalar(@nextLetters) > 1) #multiple words possible for mask.
            {
            return 0;
            }
        #$temp = $nextLetters[0];
        $mask =~ s/o/$nextLetters[0]/; #replace first blank with the single letter
        }
#only one word is possible for mask at this point
#but has it been used?
if ($wordsThatAreInserted{$mask} == 1) {
      return 1;
      }
else
      {return 0;}
};

sub intersection()
{
#two lists must be passed by reference \@sfdsfds , \@dgffdsfds
#my @union = ();
my @intersection = ();
#my @difference = ();
my %count = ();

if ($debug == 1) {print LOGG "Entering \&intersection()\n\n"}

foreach my $element (@{$_[0]} , @{$_[1]})
        {
        $count{$element}++;
        } #count singles or duplicates in the lists

@intersection = grep {($count{$_} > 1)} keys(%count); #only pass to the list duplicates not single values

if ($debug == 1) {print LOGG "Exiting \&intersection()\n\n"}
return(@intersection);
};

sub getNextPossibleLetters {
#ony run when reading / loading word list
#input $_[0] mask of word ; eg COoo
#output return list of possible next letters
my $mask = $_[0];

return keys %{$linearWordSearch{$mask}};  #return possible next letters
};
