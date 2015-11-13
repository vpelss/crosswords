#!/usr/bin/perl

#future ideas ver 3.0 meta recurse using blocks. blocks will consist of a starting word and dir and all it's crossing words

#print common walk path data with title!
#show sample of grids
#explain walks
#explain backtracking
#new grids

#allow sentences in words (strip out spaces)

use strict;

use List::Util qw(shuffle);
use Time::HiRes;
use Fcntl qw(:flock SEEK_END);
use vpvars;

#get setup variables the proper way
my $archivepath = $vpvars::archivepath;
my $archiveurl  = $vpvars::archiveurl;
my $scripturl  = $vpvars::scripturl;

$|=1; #keep it alive as long as possible as server allows
print "Content-type: text/html\n\n";
if ( -e "quickprint.txt") { print"Already running."; die("$0 is already running. Exiting.\n"); };

open(my $quickprint, ">quickprint.txt") or die "Can't open : $!";
lock($quickprint);

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

eval { &main; };     # Trap any fatal errors so the program hopefully
if ($@) {  &quickprinttofile("fatal error: $@"); &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

my $game;
my $uid;
my $message;

sub main {
my @temp;
my $x;
my $y;
my @vert;
my @horiz;

$game = time; #this will determine the folder
$uid = $in{uid}; #facebook user ID number
if ($uid eq '') {$uid='common'} #for non facebook games

srand;

$in{layouts} = 'grids';
$in{grid} = '5x5';
$in{optimalbacktrack} = 1;
#$in{wordfile} = "sympathyClues_31121";
$in{wordfile} = "MyClues_248505";
$in{walkpath} = 'crossingwords';

%in = &parse_form; #get input arguments. comment out for commandline running

&process_arguments;

$timeForCrossword = time();

$message = $message . "Loading or creating grid...\n";
&quickprinttofile($message);
if ($debug ) {print "\n\nLoading or creating grid...\n\n";}
if ($in{layouts} eq 'grids')
     {
     &load_grid( $in{grid} );
     }

if ($in{layouts} eq 'doublespaced')
     {
     print "full $in{doublespacedfull} evenodd $in{evenodd}\n\n";
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
&quickprinttofile($message);
if ($debug ) {print time()-$timeForCrossword .  " sec Numbering grid...\n\n";}
&numberBlankSquares();

$message = $message . "Loading word list...\n";
&quickprinttofile($message);
if ($debug ) {print time()-$timeForCrossword . " sec Loading word list...\n\n";}
&LoadWordList( $in{wordfile} );

#my @tt = &WordsFromLetterLists(['C','D','F','T','Z'] , ['A'] , ['T','R','E','W','Q','Z']);
#my @tt = &WordsFromLetterLists(['C','D','F','T','Z'] , [$padsEitherSide] , ['T','R','E','W','Q','Z']); #$padsEitherSide here means that there is a pad on either side so assume all letters!
#my @tt = &WordsFromMask("ooT");
#my @tt = &NthLettersFromListOfWords(2,['GOAT','HYUI','OoUY']);
#print "@tt\n\n";

if ($debug ) {print time()-$timeForCrossword . " sec Calculating word walk path...\n\n";}
if ($in{walkpath} eq 'crossingwords')
     {
     &GenerateNextWordPositionsOnBoardCrossing(); #good all purpose start anywhere!
     }
if ($in{walkpath} eq 'zigzag')
     {
     &GenerateNextWordPositionsOnBoardZigZag();
     }

#&GenerateNextWordPositionsOnBoardNumerical(); #good!
#&GenerateNextWordPositionsOnBoardDiag();
#&GenerateNextWordPositionsOnBoardAcrossThenDown(); #poor
#&GenerateNextWordPositionsOnBoardRandom(); #forget it!

$timeForCrossword = time(); #reset counter so we mesure time to find solution only

&RecursiveWords();

&quickprinttofile();
if ($debug ) {print time()-$timeForCrossword . " sec Done.\n\nNumbering clue list.\n\n";}

&quickprinttofile("Getting clues...");

$timeForCrossword = time(); #reset counter so we mesure time to find solution only

&number_clue_list();

if ($debug ) {print time()-$timeForCrossword . " sec Print solved puzzle.\n\n";}
my $solved_puzzle = "";
$solved_puzzle = &print_solved_puzzle;

if ($debug ) {print time()-$timeForCrossword . " sec Print puzzle\n\n";}
my $puzzle_string = &print_puzzle;

open (DATA, "<./templates/index.html") or die("Template file /templates/index.html does not exist");
my @DATA = <DATA>;
close (DATA);
my $template_file = join('' , @DATA);

#$archivepath = 'c:\\home\\';

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

&Quit( qq| Your crossword is at:<br><a href="$archivepath/$uid/$game/index.html">$archivepath/$uid/$game/index.html</a><br> |  );

exit;
}

sub Quit()
{
print $_[0];
unlock($quickprint);
close($quickprint);
unlink('quickprint.txt');
exit;
}

sub process_arguments {
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

#not a good idea as it may prune search tree whem we split direction? Prove
#$wordNumber = int(rand($biggestwordNumber));

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
#print "\n\n";
}

sub GenerateNextWordPositionsOnBoardNumerical
{
#create a sequential list in which we will lay down words. FIFO
#just go numerically 1 .. ??? alternating horiz / vert

for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++) #loop through all word numbers even if they don't exist
      {
      for (my $dir = 0 ; $dir < 2 ; $dir++) #loop through each direction even if it doesnt exist
      #for (my $dir = 1 ; $dir > -1 ; $dir--) #loop through each direction even if it doesnt exist
            {
            my $word = $allMasksOnBoard[$wordNumber][$dir]; # get WORD or MASK at this crossword position
            if ($word eq undef) {next;} # if this [$wordNumber][$dir] does not exists in xword grid, find next one that does
            push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
            if ($debug ) {print "($wordNumber,$dir)";}
            }
      }
#print "\n";
}

sub GenerateNextWordPositionsOnBoardRandom
{
#create a sequential list in which we will lay down words. FIFO
#just go numerically 1 .. ??? alternating horiz / vert

for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++) #loop through all word numbers even if they don't exist
      {
      for (my $dir = 0 ; $dir < 2 ; $dir++) #loop through each direction even if it doesnt exist
      #for (my $dir = 1 ; $dir > -1 ; $dir--) #loop through each direction even if it doesnt exist
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
#print "\n";
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
#print "\n";
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
#print "\n";
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
{
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
      for ($x = 0 ; $x < $in{width} ; $x++)
            {
            #for ($dir = 0 ; $dir < 2 ; $dir++) #for both across 0 and down 1 words
                  {
                  #if ( exists($ThisSquareBelongsToWordNumber[$x][$y][0]) and exists($ThisSquareBelongsToWordNumber[$x][$y][1]) )
                  #     {$crossingCells++;}
                  if ($puzzle[$x][$y]->{Letter} eq $padChar)
                       {$padCells++;}
                  if ($puzzle[$x][$y]->{Letter} eq $unoccupied)
                       {$whiteCells++;}
                  }
            }
      }
my $totalCells = $in{height} * $in{width};
#my $density = 100 * $whiteCells / $totalCells;
#$density = sprintf "%.1f", $density;
#print "Total: $totalCells Pad Cells: $padCells Density: $density\n\n";

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

sub number_clue_list {
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

sub load_grid
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

sub numberBlankSquares
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
         &quickprinttofile($message);

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

my $naiveBacktrack;
my $optimalBacktrack;
my $countprint;
my %touchingWordsForBackTrack; #global as we need to backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!
my $oldTime;
sub RecursiveWords()
{
#recursive try to lay down words using @nextWordOnBoard, will shift of, store and unshift if required
#store locally the possible words in  @possibleLetterLists
#in just the next index in a list (@NextWordPositionsOnBoard) of word position we are trying to fill

my $popWord;

#$recursiveCounts++;

%touchingWordsForBackTrack = (); #clear global indicating that we are moving forward and have cleared the backtrack state

if (scalar @nextWordOnBoard == 0) {return 1}; #if we have filled all the possible words, we are done. This breaks us out of all recursive  success loops
my %wordPosition =  %{ shift @nextWordOnBoard }; #keep in subroutine unchaged as we may need to unshift on a recursive return
my $wordNumber = $wordPosition{wordNumber};
my $dir = $wordPosition{dir};

#get all possible words for mask
my $mask = $allMasksOnBoard[$wordNumber][$dir]; # get WORD or MASK at this crossword position

#complex one 0.05 sec a call. better for more crosslinks?
#does remarkably well on big1.txt
my @possibleLetterLists = &LetterListsFor($wordNumber , $dir);
#my @wordsThatFit = sort {$b cmp $a} &WordsFromLetterLists(@possibleLetterLists);
my @wordsThatFit = shuffle &WordsFromLetterLists(@possibleLetterLists);

#simple one. 0.0002 sec a call.  better for less crosslinks?
#ignore crossing words as future mask checks will find the failures/errors. not true for some walks as there msay be no crossword checking!
#it will only work with alternating across and down checks GenerateNextWordPositionsOnBoardColRow
#my @wordsThatFit = sort {$b cmp $a} &WordsFromMask($mask);
#my @wordsThatFit = shuffle &WordsFromMask($mask);

$recursiveCount++; #count forward moving calls

my $success = 0;
while ($success == 0)
        {
        if (scalar @wordsThatFit == 0) #are there any possible words? If no backtrack
              {
              #fail to find a list of words going forward or we are out of words in a recursion so go back a word
              unshift @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
              #print "no words for word $wordNumber dir $dir\n";
              #optimal backtrack option. saves hundreds of naive backtracks!
              #get/set global touchingWords and backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!
              %touchingWordsForBackTrack = &GetTouchingWords($wordNumber,$dir);
              return 0;
              }; #no words so fail

        #try the next word that fit in this location
        $popWord = pop @wordsThatFit;
        if ($wordsThatAreInserted{$popWord} == 1) #this word is already used. fail
                  {
                 &placeMaskOnBoard($wordNumber , $dir , $mask);
                 next; #choose another word ie. pop
                  }
        else #place word
                 {
                 &placeMaskOnBoard($wordNumber , $dir , $popWord);
                 $wordsThatAreInserted{$popWord} = 1;
                 }

        $countprint++;
        #if ($countprint > 10)
        if (time() > $oldTime + 3) #print every 3 seconds
              {
              if ($debug ) {print time()-$timeForCrossword . " sec wordNumber:$wordNumber , dir:$dir $popWord optimalBacktrack:$optimalBacktrack naiveBacktrack:$naiveBacktrack recursive calls:$recursiveCount\n";}
              else {print '.';} # otherwise apache timeout directive limit is reached
              &quickprinttofile();
              $countprint = 1;
              $oldTime = time();
              }

        #attempt to lay next word
        $success = &RecursiveWords(); #lay next word in the next position
        if ($success == 1){return 1;}; #board is filled, return out of all recursive calls successfuly
#---------------
        #if we are here, the last recursive attempt to lay a word failed. So we are backtracking.
        #returning from last word which failed

        $wordsThatAreInserted{$popWord} = 0; #allow us to reuse word
        #failed so reset word to previous mask
        &placeMaskOnBoard($wordNumber , $dir , $mask);

        if ($in{optimalbacktrack} == 0)
             {
             %touchingWordsForBackTrack =(); #stop optimal recursion?
             }

        #optimal backtrack check and processing
        if (%touchingWordsForBackTrack != ())
             {
              #we are doing an optimal backtrack
              if ($touchingWordsForBackTrack{$wordNumber}{$dir} == 1) {
                   #we have hit the optimal target. turn off optimal backtrack
                   #print "optimal: word:$wordNumber dir:$dir \n";
                   %touchingWordsForBackTrack = ();
                   }
              else {
                    #still in optimal backtrack so keep going back
                    unshift @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};
                    $optimalBacktrack++;
                    return 0;
                    }
              }

        $naiveBacktrack++;
        next; #naive backtrack
        }

die('never get here'); #never get here
}

sub GetTouchingWords()
{
#input: word number and direcction
#output: hash (quick access) of words number and direction of words that cross and adjoin (horiz - above/below , vert left/right)
# $touchingWords{#}{dir} = 1

my %touchingWords;
my $wordNumber = $_[0];
my $dir = $_[1];

my $x;
my $y;
my $crossingWordDir;
my $letterPosition;
my $crossingWordNumber;
my $adjoiningWordNumber;

#print "for word $wordNumber dir $dir\n";
#for adjoining search
my $divX;
my $divY;
if ($dir == 0) {
       $divX = 0;
       $divY = 1;
       }
 else {
       $divX = 1;
       $divY = 0;
        }

my @wordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]};
foreach $letterPosition (@wordLetterPositions)
  {
  $x = $letterPosition->[0];
  $y = $letterPosition->[1];
  $crossingWordDir =  $OppositeDirection[$dir];

  #find and mark crossing words
  $crossingWordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$crossingWordDir];
  $touchingWords{$crossingWordNumber}{$crossingWordDir} = 1;
  #print "crossing word $crossingWordNumber\n";

  #find and mark adjoining words
  $adjoiningWordNumber = $ThisSquareBelongsToWordNumber[$x + $divX][$y + $divY][$dir];
  if ($adjoiningWordNumber > 0) {
       $touchingWords{$adjoiningWordNumber}{$dir} = 1;
       #print "adjoining word $adjoiningWordNumber\n";
       }
  $adjoiningWordNumber = $ThisSquareBelongsToWordNumber[$x - $divX][$y - $divY][$dir];
  if ($adjoiningWordNumber > 0) {
       $touchingWords{$adjoiningWordNumber}{$dir} = 1;
       #print "adjoining word $adjoiningWordNumber\n";
       }
  }
return %touchingWords;
}

sub GetCrossingWords()
{
#input: word number and direcction
#output: hash (quick access) of words number and direction of words that cross and adjoin (horiz - above/below , vert left/right)
# $touchingWords{#}{dir} = 1

my @crossingWords;
my $wordNumber = $_[0];
my $dir = $_[1];

my $x;
my $y;
my $crossingWordDir;
my $letterPosition;
my $crossingWordNumber;
#my $adjoiningWordNumber;

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
     #quickprinttofile;
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

sub quickprinttofile {
my $message = $_[0];
my ($x , $y);
my $line;
my $string;
my $time;
$time =  time - $timeForCrossword;

#open(my $quickprint, ">quickprint.txt") or die "Can't open : $!";

#limit script run time!
if ($time > $timelimit)
     {
     &Quit(  "Time limit exceeded<br>\n\n" );
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

if ($message ne "") {$string = "$message";}

print $quickprint "$string";

#$quickprint->flush();
seek($quickprint, 0 , 0);
#close($quickprint); #need to close so it erases file
#open($quickprint, ">quickprint.txt") or die "Can't open : $!";
};

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
#until ( ($puzzle[$x][$y]->{Letter} =~ /$padChar/) or ($puzzle[$x][$y]->{Letter} =~ /$padCharTemp/) or &outsideCrossword($x,$y) )
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

=pod
$temp2 = 0;
#see how many times we have crossed another word
if ($Ignore_Crosses == 0)
     {
     foreach $temp (@temp)
         {
         if ($puzzle[$x][$y]->{Letter} =~ /\w/)
              {
              $temp2++;
              }

         $x = $x + (not $dir);
         $y = $y + $dir;
         }
     if ($temp2 < 1)
          {
          return($_[0] , $_[1] , $dir , '')
          } #fail if we don't cross at all
     }
=cut

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
         #push @{$puzzle[$x][$y]->{WordsAtPos}} , $word; #add the word to an array for EACH crossword position so we know what words belong to what square

         $x = $x + (not $dir);
         $y = $y + $dir;
         $temp2 = $temp2 + 1;
         }
#pad at end of word to avoid word butting
#if ($temp2 != 0) {$puzzle[$x][$y]->{Letter} = $padChar};
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

unlock($quickprint);
close($quickprint);
unlink('quickprint.txt');

if ($debug == 0) {print "Epic fail...."; exit;}

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
exit -1;
};
