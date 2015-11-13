#!/usr/bin/perl


use List::Util 'shuffle';
use Time::HiRes;

my $archivepath; #set in vars.cgi
my $archiveurl; #set in vars.cgi
my $scripturl; #set in vars.cgi
require "vars.cgi";  #load up common variables and routines. // &cgierr

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
#$letterPositions[word #][dir] an array of all the word letter positions [[x,y],[x,y]....]
#set $letterPositions[$numberCount][$dir] = [@TempLetterPositions]; #an annonomyous array reference of $x,$y pairs of all letters in the word
#get my @WordLetterPositions = @{$letterPositionsOfWord[$wordNumber][$dir]}
#used to find crossing words fast with @ThisSquareBelongsToWordNumber

my @ThisSquareBelongsToWordNumber;
# $ThisSquareBelongsToWordNumber[x][y][0] returns the word number this square belongs to
#set $ThisSquareBelongsToWordNumber[$xx][$yy][$dir] = $numberCount
#get my $crossingwordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$crossingWordDir]

my @NextWordPositionsOnBoard;
#all words position on board used for cycling through word placements, etc
# [{wordNumber => $wordNumber, dir => $dir},{},{}...]
#$NextWordPositionsOnBoard[]{wordNumber} $NextWordPositionsOnBoard[]{dir}

my @nextLetterPositionsOnBoard;
#all letter position on board used for cycling through letter placements, etc
# [{x => $x, y => $y} , , ]
#$nextLetterPositionsOnBoard[]{x} $NextWordPositionsOnBoard[]{y}

my @PositionInWord;
#$PositionInWord[x][y][dir] returns the pos of letter in the word this square belongs to starting at 0
#set $PositionInWord[$xx][$yy][$dir] = $PositionCount
#get  my $NthLetterPosition = $PositionInWord[$x][$y][$crossingWordDir]

my %wordsThatAreInserted = ();
#hash of hashes.   $wordsThatAreInserted{word} = 1 or undef
#used to prevent duplicate words on the board

my %wordlengths; #used to identify word lengths possible on the grid. $wordLength{6} = 1. we will only load words of lengths that exist!

my %WordListByMask = (); #no longer used. Not much faster than regex routies
# keys $wordListByMask{oYo} returns a list of all words fitting the mask
#created by taking each word, then creating a binary mask for the word and
#$wordListByMask{ooRo}{WORD}=1
#$wordListByMask{WoRo}{WORD}=1 etc
#huge database but very fast search for words fitting a mask or pattern

my %wordListBy_WordLength_Letter_LetterPosition; #no longer used
#array of [$wordLength][ord($letter)][$letterPosition] returns hash of words that fit the bill
#set $wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]{$word} = 1
#get keys %{$wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]}
#a hash, instead of a list, is used so we don't have duplicate words

my %linearWordSearch  = (); #no longer used
#very fast for finding the next possible letters in a word
#$linearWordSearch{mask}{key1 , key2} and it will return a list of keys (so there are no duplicates) representing the next possible letters.
#@letters = keys %{$linearWordSearch{$mask}};
#mask must be a prefix mask ie: TOOLooooo

my $padChar = 'x';
my $unoccupied = 'o';
$padsEitherSide = 'padsEitherSide';
#$dir 0 = horiz 1 = vertical
my %clues;
my $hints_across;
my $hints_down;

my $debug = 0;
my $biggestwordNumber;
my @OppositeDirection;$OppositeDirection[0] = 1;$OppositeDirection[1] = 0; #instead of using (not)

my $timeForCrossword;
my $countMe = 1;

eval { &main; };                            # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.


sub main {
my @temp;
my $x;
my $y;
my @vert;
my @horiz;

srand;
print "Content-type: text/html\n\n";

#%in = &parse_form; #get input arguments

#$in{wordfile} = "./wordlists/sympathyClues_31121/";
$in{wordfile} = "./wordlists/MyClues_248505/";

&process_arguments;

#&load_grid('grids\3x3.txt');
#&load_grid('grids\4x4.txt');
#&load_grid('grids\5x5.txt');
#&load_grid('grids\6x6.txt');
#&load_grid('grids\7x7.txt');
#&load_grid('grids\big1.txt');
&load_grid('grids\15x15.txt');
#&load_grid('grids\21x21.txt');
#&load_grid('grids\01.txt');
#&load_grid('grids\double.txt');
#&load_grid('grids\doublebase.txt');
#&load_grid('grids\doublebase13x13.txt');
#&load_grid('grids\doublebase11x11.txt');
#&load_grid('grids\doublebase9x9.txt');
#&load_grid('grids\doublebase7x7.txt');
#&load_grid('grids\doublebase6x6.txt');


&numberBlankSquares();
&load_word_list( $in{wordfile} );

#my @tt = &WordsFromLetterLists(['C','D','F','T','Z'] , ['A'] , ['T','R','E','W','Q','Z']);
#my @ttt = &WordsFromLetterListsR(['C','D','F','T','Z'] , ['A'] , ['T','R','E','W','Q','Z']);
#my @tt = &WordsFromLetterLists(['C','D','F','T','Z'] , [$padsEitherSide] , ['T','R','E','W','Q','Z']); #unoccupied here means that there is a pad on either side so assume all letters!
#my @tt = &WordsFromLetterLists(['C','D','F','T','Z'] , [] , ['T','R','E','W','Q','Z']); #unoccupied here means that there is a pad on either side so assume all letters!
#my @tt = &WordsFromLetterLists(['U'] , ['T'] , ['R'],['P']);
#my @tt = &WordsFromLetterLists(['C','B'] , ['A'] , ['T','R']);
#my @tt = &WordsFromLetterLists(['C','B'] , [] , ['T','R']);
#my @tt = &WordsFromLetterLists([] , [] , ['T','R']);
#my @tt = &WordsFromMask("ooT");
#my @tt = &WordsFromMask('GOAT');
#my @tt = &NthLettersFromListOfWords(2,['GOAT','HYUI','OoUY']);
#@tt = keys %{$linearWordSearch{"Booo"}};
#print "@tt\n\n";
#print "@ttt\n\n";

&GenerateNextWordPositionsOnBoardCrossing(); #good all purpose start anywhere!
#&GenerateNextWordPositionsOnBoardNumerical(); #good!
#&GenerateNextWordPositionsOnBoardDiag();
#&GenerateNextWordPositionsOnBoardZigZag();
#&GenerateNextWordPositionsOnBoardAcrossThenDown(); #poor
#&GenerateNextWordPositionsOnBoardRandom(); #forget it!

#&GenerateNextLetterPositionsOnBoardFlat(); #8 sec double
#&GenerateNextLetterPositionsOnBoardZigZag(); #8 sec double
#&GenerateNextLetterPositionsOnBoardDiag(); #4 sec double
#&GenerateNextLetterPositionsOnBoardRandom();
#&GenerateNextLetterPositionsOnBoardSnakeWalk(); #19 sec double . too many options early on

#&GeneratenextLetterPositionsOnBoardSwitchWalk();

$timeForCrossword = time();

&quickprinttofile();

#&RecursiveLetter();
&RecursiveWords();

print "wordNumber:$wordNumber , dir:$dir $popWord optimalBacktrack:$optimalBacktrack naiveBacktrack:$naiveBacktrack recursive calls:$countMe\n\n";
&quickprinttofile();
print "\n\ndone\n\n";

&number_clue_list();

my $solved_puzzle = "";
$solved_puzzle = &print_solved_puzzle;
my $puzzle_string = &print_puzzle;

open (DATA, "<./templates/index.html") or die("Template file /templates/index.html does not exist");
my @DATA = <DATA>;
close (DATA);
my $template_file = join('' , @DATA);

$archivepath = 'c:\\home\\';

$template_file =~ s/<%answers%>/$solved_puzzle/g;
$template_file =~ s/<%across%>/$hints_across/g;
$template_file =~ s/<%down%>/$hints_down/g;
$template_file =~ s/<%down%>/$hints_down/g;
$template_file =~ s/<%puzzle%>/$puzzle_string/g;
$template_file =~ s/\%archivepath\%/$archivepath/g;
$template_file =~ s/\%archiveurl\%/$archiveurl/g;
$template_file =~ s/\%scripturl\%/$scripturl/g;
my $uid = $in{uid}; #facebook user ID number
if ($uid eq '') {$uid='common'} #for non facebook games
$template_file =~ s/\%uid\%/$uid/g;
my $name = $in{name}; #facebook user name
$name =~ s/\%20/ /g; #get rid of %20 for spaces
$template_file =~ s/\%name\%/$name/g;

#archive the puzzle!
my $game = time;
#$filename .= ".html";

$template_file =~ s/\%game\%/$game/g;
print $template_file;

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

print "\n\n";
exit;
}

sub GenerateNextWordPositionsOnBoardCrossing
{
#start with 1 horiz.
#find all crossing words
#find all their crossing words.
#only add # and direction once!
#FIFO

my @wordLetterPositions = ();
my %alreadyInList = (); # $alreadyInList{number}{direction} = 1 if already in list
#my $currentWord = 1;
#my $currentDir = 0;
my $wordNumber = 1;
my $dir = 0;
#if ($allMasksOnBoard[$currentWord][$currentDir] == undef) # oops no horizontal #1 word. go vertical
     #{$currentDir = 1;}
if ($allMasksOnBoard[$currentWord][$dir] == undef) # oops no horizontal #1 word. go vertical
     {$dir = 1;}
my @toDoList = (); #list of words and directions to process. ((1,0) , (2,0) , .... ) shift off and push on so we do in an orderly fasion!
#push @toDoList , [$currentWord,$currentDir];
push @toDoList , [$wordNumber,$dir];
#$alreadyInList{$currentWord}{$currentDir} = 1;
$alreadyInList{$wordNumber}{$dir} = 1;
#push @nextWordOnBoard , {wordNumber => $currentWord, dir => $currentDir};
push @nextWordOnBoard , {wordNumber => $wordNumber, dir => $dir};

while ( scalar @toDoList > 0 )
        {
        #($currentWord , $currentDir) = @{ shift @toDoList };
        #print "looking at:($currentWord,$currentDir)\n";
        #my @crossingWords = &GetCrossingWords( $currentWord , $currentDir );
        ($wordNumber , $dir) = @{ shift @toDoList };
        print "looking at:($wordNumber,$dir)\n";
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
                print "($wordNumber,$dir)\n";
                }
        }
foreach $item (@nextWordOnBoard)
         {
         print "($item->{wordNumber},$item->{dir})";
         }
print "\n\n";
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
            print "($wordNumber,$dir)";
            }
      }
print "\n\n";
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
     print "(${$nextWordOnBoard}{'wordNumber'} , ${$nextWordOnBoard}{'dir'} )";
      }
print "\n\n";
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
            print "($wordNumber,$dir)";
            }
      }
print "\n\n";
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
                          print "($x,$y)word#:$wordNumber,dir:$dir | ";
                          }
                  }
             }
        }
until ( ($x == $in{width} - 1) and ($y == $in{height} - 1) );
print "\n\n";
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
    print "($x,$y)";
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
                          print "($x,$y)word#:$wordNumber,dir:$dir | ";
                          }
                  }
         }
    }
until ( ($x >= $in{width} - 1) and ($y >= $in{height} - 1) );

}

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
                  push @nextLetterPositionsOnBoard , {x => $x, y => $y};
                  print "($x,$y)";
                  }
             }
         }
print "\n\n";
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
        #print "($x,$y)";
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
    print "($x,$y)";
    #process cursor position
    if ($puzzle[$x][$y]->{Letter} ne $padChar) {
         push @nextLetterPositionsOnBoard , {x => $x, y => $y};
         }
    }
until ( ($x >= $in{width} - 1) and ($y >= $in{height} - 1) );
}

sub GenerateNextLetterPositionsOnBoardRandom
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
                  push @nextLetterPositionsOnBoard , {x => $x, y => $y};
                  print "($x,$y)";
                  }
             }
         }
print "\n\n";
@nextLetterPositionsOnBoard = shuffle @nextLetterPositionsOnBoard
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
                     print "dir:$dir walkStep:$walkStep walkLength:$walkLength ($x,$y)\n";
                     push @nextLetterPositionsOnBoard , {x => $x, y => $y};
                     }
                $x = $x + (not $dir);
                $y = $y + $dir;
                }
          }
    }
until ($walkLength > $in{height} - 1);

print "\n\n";
}

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

for ($dir=0 ; $dir < 2 ; $dir++)
     {
     $hints = '';
     for ($wordNumber=1 ; $wordNumber <= $biggestwordNumber ; $wordNumber++)
          {
          $word = $allMasksOnBoard[$wordNumber][$dir];
          if ($word ne undef)
               {
               $wordLetterPositions = &javascriptArrayFromLetterPositions(@{$letterPositionsOfWord[$wordNumber][$dir]}); #clear last one
               $x = $letterPositionsOfWord[$wordNumber][$dir]->[0]->[0];
               $y = $letterPositionsOfWord[$wordNumber][$dir]->[0]->[1];
               $hints .= qq|
                    $wordNumber\. <a href="\#self" id="$word" class="clues" ONCLICK="choose('$word' , $x , $y , [$wordLetterPositions]);">$clues{$word}</a>
                    &nbsp;&nbsp;&nbsp;&nbsp;
                    <font size=-1><i><A ONCLICK="if (this.innerHTML=='show') {this.innerHTML='$word'} else {this.innerHTML='show'}" HREF="\#self">show</A></i></font></br>
                    |;
               }
          }
     if ($dir == 0) {$hints_across = $hints}
     if ($dir == 1) {$hints_down = $hints}
     }
}

sub process_arguments {
#process input arguments
# Test inputs to see if they are valid and set defaults

#defaults
if ( (not $in{timeout}) or ($in{timeout} !~ /^\d+$/ ) ) { $in{timeout} = 5; }
#if (not $in{wordfile}){$in{wordfile} = "words/CrosswordExpress/"}
#if (not $in{wordfile}){$in{wordfile} = "words/CrosswordExpressExtra/"}
if (not $in{wordfile}){$in{wordfile} = "./wordlists/MyClues_248505/"}

#set bounds
if  ($in{timeout} > 30)  { $in{timeout} = 30; }
};

sub load_grid
{
my $filename = $_[0];
my ($x , $y);
$in{height} = 0;
$in{width} = 0;
my $square;
my $temp = 0;

open (DATA, "<$filename") or die("Word file $filename does not exist");
foreach $line (<DATA>)
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

print "width:$in{width} height:$in{height}\n\n";

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
                  $wordLength = &possibleWordSize($x,$y,$dir);
                  print "x:$x,y:$y,dir:$dir len:$wordLength \n";
                  if ($wordLength > 2) #words of length 0 are returned if we are on a pad character. ignore. also counts 1 letter words and 2 letter word
                    {
                    $wordLength{$wordLength} = 1; #mark globally that there is a word of this length
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
                         print "Word:$numberCount Dir:$dir\n";
                         foreach my $letterPosition (@TempLetterPositions)
                                 {
                                 $xx = $letterPosition->[0];
                                 $yy = $letterPosition->[1];
                                 $ThisSquareBelongsToWordNumber[$xx][$yy][$dir] = $numberCount;
                                 $PositionInWord[$xx][$yy][$dir] = $PositionCount;
                                 print "x:$xx y:$yy pos:$PositionCount\n";
                                 $PositionCount++;
                                 $blankWord = "$blankWord$unoccupied";
                                 }
                         $allMasksOnBoard[$numberCount][$dir] = $blankWord;
                         $letterPositionsOfWord[$numberCount][$dir] = [@TempLetterPositions]; #an annonomyous array reference of $x,$y pairs of all letters in the word
                         print "\n";
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
print "Grid has words of lenths : ";
foreach $wordLength (keys %wordLength)
         {
         print "$wordLength ,";
         }
print "\nDensity:$density\% , Interlock:$interlock\% , Crossing:$crossingCells , White:$whiteCells , Total:$totalCells \n\n";
};

sub load_word_list {
my $filename = $_[0];
#my @DATA;
my $line;
my $word;
my $clue;
my $wordLength;
my $letterPosition;
my $letter;
my $temp;
my $mask;
my %letterFreq; # $letterFreq{wordlength}{letterpos}{letter} ++
my $lineCount;

$t = time();
print "loading words...\n";

my $directory = "$in{wordfile}/words/";
#read word and clue file
if (not -d $directory) {die "directory $directory does not exist"};
#open (DATA, "<$filename") or die("Word file $filename does not exist");

=pod
#build binary mask lists for all the word lengths 3-15
# @{ $binaryMasks{ $numberOfLetters ) }
for ( my $numberOfLetters = 3 ; $numberOfLetters < 21 ; $numberOfLetters++)
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
foreach $wordLength ( keys %wordLength)
         {
         $filename = "$directory$wordLength\.txt";
         #$filename = "$directory/all.txt";
         open (DATA, "<$filename") or die("Word file $filename does not exist");
         #my @words =  <DATA>;
         foreach $word (<DATA>)
                  {
                  $word =~ s/\n//g; #remove line return
                  $word =~ s/\r//g; #remove line return
                  if ($word eq '') {next} #blank line. toss
                  $word = uc($word); #all words must be uppercase for standard, display and search reasons.
                  $wordsOfLength{$wordLength}++; #global var for statistics
                  my @lettersInWord =  split('' , $word);

                  #letter by letter builds here
                  $letterPosition = 0;
                  #prep for new fast linear word search : $linearWordSearch{mask}
                  $mask = $word;
                  $mask =~ s/\S/o/g; #build a mask with ooooooooo of wordlength

                  foreach $letter (@lettersInWord)
                           {
                           #build new fast linear word search : $linearWordSearch{mask}
                           $linearWordSearch{$mask}{ substr($word,$letterPosition,1) } = 1 ; #add letter for $letterPosition to set of hash keys for this $mask
                           substr ( $mask , $letterPosition , 1 , $letter); #change mask with next letter added to it Cooo to COoo

                           #build $wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]{$word} = 1;
                           #create %WordListBy_WordLength_Letter_LetterPosition : a hash of words for each letter in each letter
                           #add word to a hash (and therefore a list using keys) accessed by an array indexed by [word length][ord(Letter)][LettePosition] with true value for quick lookup!
                           $wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]{$word} = 1;
                           #print keys %{$wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]};
                           #print "\n\n\n\n";

                           $letterPosition++;
                           }

                  #build $wordsOfLengthString[$wordLength] string
                  if ($wordsOfLengthString[$wordLength] eq '') {$wordsOfLengthString[$wordLength] = ','} #start string of words with a coma
                  $wordsOfLengthString[$wordLength] = "$wordsOfLengthString[$wordLength]$word,"; #build a comma delimited string of each possible word length
                  }
         close (DATA);
         }

=pod
foreach $line (<DATA>)
         {
         $line =~ s/\n//g; #remove line return
         ($word , $clue) = split(/\|/,$line);
         $lineCount++;

         $word = uc($word); #all words must be uppercase for standard, display and search reasons.
         $wordLength = length($word);
         if ( $wordLength{$wordLength} != 1 ) {next;}; #skip words that are of a length that are not on grid

         #store clue for word
         if (exists $clues{$word}) #does clue for word already exist?
             {
             if (rand() < 0.5) {$clues{$word} = $clue;} #We already have a clue for this word. 50% chance we will use new clue. gives gausian like curve (we want a square curve:all possibilties equal), but adaquate for 5 or less clues.

             next; #go get next word in the list as we have already processed this $word
             }
         else #no clue yet
             {
             $clues{$word} = $clue;
             }

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
               #print "$maskedWord : @kkeys\n\n";
               }

         if ($wordsOfLengthString[$wordLength] eq '') {$wordsOfLengthString[$wordLength] = ','} #start string of words with a coma
         $wordsOfLengthString[$wordLength] = "$wordsOfLengthString[$wordLength]$word,"; #build a comma delimited string of each possible word length

         $wordsOfLength{$wordLength}++;

         my @LettersInWord =  split('' , $word);
         $letterPosition = 0;
         foreach $letter (@LettersInWord)
                  {#create %WordListBy_WordLength_Letter_LetterPosition : a hash of words for each letter in each letter
                   #add word to a hash (and therefore a list using keys) accessed by an array indexed by [word length][ord(Letter)][LettePosition] with true value for quick lookup!
                  $wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]{$word} = 1;
                  $letterPosition++;
                  };

         $letterPosition = 0;
         foreach $letter (@LettersInWord)
                  {#Bulid up a record of how frequently a letter is in the nth letter of a word of length m.
                  $letterFreq{$wordLength}{$letterPosition}{$letter}++;
                  $letterPosition++;
                  };

         #old fast linear word search
         # $linearWordSearch{1st}{2nd}{3rd}.....
         if (! exists( $linearWordSearchOld[$wordLength] ))
             {
             $linearWordSearchOld[$wordLength] = {}; #create new hash as it doesn't exist
             }
         my $refToNextHash = $linearWordSearchOld[$wordLength];
         foreach $letter (@LettersInWord)
                  {
                  if (! exists(${$refToNextHash}{$letter}))
                      {
                      ${$refToNextHash}{$letter} = {}; #create new hash as it doesn't exist
                      };
                  $refToNextHash = ${$refToNextHash}{$letter};
                  }
         }
close (DATA);
=cut

#done loading words. Let's calculate some statistics

foreach $length (sort keys %wordsOfLength)
     {
     print "$length : $wordsOfLength{$length}\n";
     $wordCount = $wordCount + $wordsOfLength{$length};
     }

$tt = time() - $t;
print "$lineCount lines and $wordCount words loaded in $tt sec \n\n";
}

sub IsWordAlreadyUsed() {
#input of mask WORooooo
#check to see if all possible letters 'o' are singles. If so word is unique. then see if word has been used
#saves us from filling in a whole word on letter fills only to have to backtrack
my $mask = $_[0];
my @nextLetters;

while ($mask =~ /o/) { #see if we get single letters until end of word
        @nextLetters = &getNextPossibleLetters($mask);
        if (scalar(@nextLetters) > 1) #multiple words possible for mask.
            {
            return 0;
            }
        $_temp = $nextLetters[0];
        $mask =~ s/o/$nextLetters[0]/; #replace first blank with the single letter
        }
#only one word is possible for mask at this point
#but has it been used?
if ($wordsThatAreInserted{$mask} == 1)
      {return 1;}
else
      {return 0;}
};

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
     if (scalar( @lettersVert) == 1) { #only one letter possible. The word may be unique. so check to see if this word is already used
         if (&IsWordAlreadyUsed($mask)) {
              return (); #return empty as this word is already used
              }
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
     if (scalar( @lettersHoriz) == 1) { #only one letter possible. The worrd may be unique. so check to see if this word is already used
         if (&IsWordAlreadyUsed($mask)) {
               return (); #return empty as this word is already used
               }
         }
     }

if (($isHorizWord) and ($isVertWord)) { #there is a horiz and vert word at this cell. find inersection of possible letters
     @lettersThatFit = intersection(\@lettersHoriz , \@lettersVert);
     return @lettersThatFit;
     }
if ((not $isHorizWord) and ($isVertWord)) { #there is only a vertical word at this cell
     return @lettersVert;
     }
if (($isHorizWord) and (not $isVertWord)) { #there is only a horizontal word at this cell
     return @lettersHoriz;
     }
die('should not get to end of letterPossibleAt()');
};

sub lettersPossibleAtCellByMask()
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
my $letterPosition;

#find vert mask and possible letters
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
if ($wordNumber > 0) { #there is a vert mask
     $isVertWord = 1;
     $mask = $allMasksOnBoard[$wordNumber][1]; # get WORD or MASK at this crossword position
     $letterPosition = $PositionInWord[$x][$y][1];
     @lettersVert = &LettersFromMaskAndPos($mask , $letterPosition);
     #can return () if only a single word is possible and word is already placed
     if ( scalar @lettersVert == 0 ) { #can return () if only a single word is possible and word is already placed
           return ();
           #die ("no \@lettersVert. impossible mask:$mask wordNumber:$wordNumber letterPosition:$letterPosition");
           }

     if (scalar( @lettersVert) == 1) { #only one letter possible. The word may be unique. so check to see if this word is already used
         if (&IsWordAlreadyUsed($mask)) {
              return (); #return empty as this word is already used
              }
         }
     }

#find horiz mask and possible letters
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
if ($wordNumber > 0) { #there is a horiz mask
     $isHorizWord = 1;
     $mask = $allMasksOnBoard[$wordNumber][0]; # get WORD or MASK at this crossword position
     $letterPosition = $PositionInWord[$x][$y][0];
     @lettersHoriz = &LettersFromMaskAndPos($mask , $letterPosition);
     if ( scalar @lettersHoriz == 0 ) {#can return () if only a single word is possible and word is already placed
          return ();
          #die ("no \@lettersHoriz. impossible mask:$mask wordNumber:$wordNumber letterPosition:$letterPosition");
          }
     if (scalar( @lettersHoriz) == 1) { #only one letter possible. The worrd may be unique. so check to see if this word is already used
         if (&IsWordAlreadyUsed($mask)) {
               return (); #return empty as this word is already used
               }
         }
     }

if (($isHorizWord) and ($isVertWord)) { #there is a horiz and vert word at this cell. find inersection of possible letters
     @lettersThatFit = intersection(\@lettersHoriz , \@lettersVert);
     return @lettersThatFit;
     }
if ((not $isHorizWord) and ($isVertWord)) { #there is only a vertical word at this cell
     return @lettersVert;
     }
if (($isHorizWord) and (not $isVertWord)) { #there is only a horizontal word at this cell
     return @lettersHoriz;
     }
die('should not get to end of letterPossibleAt()');
};

my $optimal;
my $forward;
my $backtrackFromX;
my $backtrackFromY;
sub RecursiveLetter()
{
#recursive benefits, leaves breadcrumb for backtrack so we do not need to follow an index #
#do not need a separate data structure for possible letters
#this routine assumes that we are using only $linearWordSearch to find letters
#no inputs
#returns 0=backtrack 1=done
#uses globals $backtrackTargetX  $backtrackTargetY
#recursive try to lay down letters using @NextLetterOnBoard, will shift of, store and unshift if required
#store locally the possible letters in  @possibleLetterLists

$countMe++; #for quick print
$recursiveCounts++;
$tt = time() - $timeForCrossword;;

$timePerRecursiveCall = $tt/$recursiveCounts;

my $x;
my $y;
my @lettersThatFit;
my %lettersThatFit; #for letter frequency version. Faster find and delete when searching key list
my $popLetter;
my $mask;
my @lettersHoriz;
my @lettersVert;
my $wordNumber;
my $success;

$forward = 1; #global
$optimal = 0; #global
#required to know if @lettersThatFit failed moving forward or from a backtrack.
#if we are moving back from a backtrack we CAN NOT use an optimal backtrack again as we have not exhausted a non optimal solution!

if ( scalar @nextLetterPositionsOnBoard == 0 ) { #puzzle is done
      return 1;
      }; #if we have filled all the possible words, we are done. This breaks us out of all recursive  success loops. starts a cascade or return 1 ant end of routines

my %cellPosition =  %{ shift @nextLetterPositionsOnBoard }; #keep %cellPosition in subroutine unchaged as we may need to unshift on a recursive return
$x = $cellPosition{x};
$y = $cellPosition{y};

@lettersThatFit = &lettersPossibleAtCell($x,$y); # 0.000059 sec per call
#@lettersThatFit = &lettersPossibleAtCellByMask($x,$y); # 0.009 sec per call

#@lettersThatFit = shuffle &lettersPossibleAtCell($x,$y); # 0.000059 sec per call
#@lettersThatFit = shuffle &lettersPossibleAtCellByMask($x,$y); # 0.009 sec per call

#keep trying the next possible letter from the pool on entering routine from above (going forward through letter list)
#or
#internally from a backtrack (going backward)!
$success = 0;
while ($success == 0)
        {
        if (scalar @lettersThatFit == 0) #no more Lettersto try if going forward. out of letters if going backwards. backtrack until we reach x - 1 or y - 1 .
              {
              if ($forward == 1) #only attempt optimal backtrack on forward direction as partial word above, if changed, may allow for a good fits that may be missed. Seems to hold for other walks!
                   {
                   if ( $puzzle[$x-1][$y]->{Letter} =~ /[A-Z]/  or  $puzzle[$x][$y-1]->{Letter} =~ /[A-Z]/  )
                        #only set optimal if there is a horiz or vert cell to backtrack to. One with a capital letter laid down
                        #required for grids with pads
                        {
                        #&quickprinttofile();
                        $optimal = 1;
                        $backtrackFromX  = $x;
                        $backtrackFromY  = $y;
                        }
                   }
              unshift @nextLetterPositionsOnBoard , {x => $x, y => $y}; #always unshift our current position back on to @nextLetterPositionsOnBoard when we return!
              #&quickprinttofile();
              return 0;
              }; #no Letters so fail

=pod
        #choose next letter based on letterFrequency
        #@lettersThatFit{@lettersThatFit} = (1) x @lettersThatFit;
        #@lettersThatFit{@lettersThatFit} = 1;
        if (rand(100) < 50)
        #if (rand(100) < -1)
            { #occasionally choose the most frequent letter
            foreach $letter (@letterFrequency)
                 {
                 if (exists $lettersThatFit{$letter})
                      {
                      #a letter is found, save, remove from hash lettersThatFit and break out of loop
                      $popLetter = delete $lettersThatFit{$letter};
                      last;
                      }
                 }
            }
        else #occasionally just chose the next letter
            {
            @temp = keys %lettersThatFit;
            $temp = pop @temp;
            $popLetter = delete $lettersThatFit{$temp};
            }
=cut

        #try the next letter that fit in this location
        $popLetter = pop @lettersThatFit;

        &SetXY($x,$y,$popLetter);

       #see if word is already selected. If so, fail + backtrack
       #if it is not, mark this word as on the board
        $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
        if ($wordNumber > 0) {$mask = $allMasksOnBoard[$wordNumber][0];}
        else {$mask='o';} #ignore as this is just a letter, not a word
        if ($mask !~ /o/) #full word?
             {
             $wordsThatAreInserted{$mask} = 1;
=pod
             if ($wordsThatAreInserted{$mask} == 1) #this word is already used. fail
                  {
                 &SetXY($x,$y,$unoccupied);
                 next; #choose another letter
                  }
             else
                 {
                 $wordsThatAreInserted{$mask} = 1;
                 }
=cut
             }

        $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
        if ($wordNumber > 0) {$mask = $allMasksOnBoard[$wordNumber][1];}
        else {$mask='o';}  #ignore as this is just a letter, not a word
        if ($mask !~ /o/)  #full word?
             {
             $wordsThatAreInserted{$mask} = 1;
=pod
             if ($wordsThatAreInserted{$mask} == 1) #this word is already used. fail
                  {
                 &SetXY($x,$y,$unoccupied);
                 next;
                  }
             else
                 {
                 $wordsThatAreInserted{$mask} = 1;
                 }
=cut
             }

     if (rand() * 10000 < 2)
         {
         print "time:$tt , RecursiveCalls:$recursiveCounts , TimePerCall:$timePerRecursiveCall\n";
         print "optimal saves:$optimalBacktrack \n";
         print "Cell:($x,$y) , From:($backtrackFromX,$backtrackFromY)\n";
         print "all:(@lettersThatFit) Horiz:(@lettersHoriz) Vert:(@lettersVert)\n";
         print "new call \n";
         print "-------------------\n";
         quickprinttofile();
         }

        #RECURSIVE CALL
        $success = &RecursiveLetter(); #lay next Letter in the next position if possible. only return 1 if puzzle is done. 0 if we are backtracking

        if ($success == 1){return 1;}; #board is filled, return out of all recursive calls successfuly

        # backtrack entry starting point. if we are here, the last recursive attempt to lay a letter failed. @lettersThatFit == () So we are backtracking.
        #OR
        #we are in an optimal backtrack return

        $forward = 0; #do not allow or trigger an optimal backtrack if we are already backtracking.

        #remove mask (possibly a word) from $wordsThatAreInserted both horiz and vert
        $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][0];
        $wordsThatAreInserted{$allMasksOnBoard[$wordNumber][0]} = 0;
        $wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][1];
        $wordsThatAreInserted{$allMasksOnBoard[$wordNumber][1]} = 0;
        &SetXY($x,$y,$unoccupied);  #failed so reset letter to $unoccupied = o

        #next; #uncomment for for naive only

        if ($optimal == 0) {
             next;
             }

        #this is optimal code

        #if ( (($backtrackFromX - 1) == $x ) and ($backtrackFromY == $y) )
        if ( ($backtrackFromX  > $x) and ($backtrackFromY == $y) ) #allowing all previous x values should work for random walk
               { #at optimal backtrack target
               $optimal = 0;
               next;
               } #We are in the backtrack target cell . see if any old letters we can use

        quickprinttofile();
        #if ( ($backtrackFromX == $x ) and (($backtrackFromY - 1) == $y) )
        if ( ($backtrackFromX == $x ) and ($backtrackFromY > $y) ) #allowing all previous y values should work for random walk
               { #at optimal backtrack target
               $optimal = 0;
               next;
               } #We are in the backtrack target cell . see if any old letters we can use

        #we are still backtracking to optimal backtrack target
        #keep speeding through naive backtracks until we hit optimal backtrack target, then try another letter from @lettersThatFit
        $optimalBacktrack++;
        unshift @nextLetterPositionsOnBoard , {x => $x, y => $y}; #always unshift when we return!
        return 0;
        }
};

my %touchingWordsForBackTrack; #global as we need to backtrack to the first  member of it we encounter. if not == () we are in a backtrack state!
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

$countMe++; #count forward moving calls

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
        if ($countprint > 1000)
              {
              print "wordNumber:$wordNumber , dir:$dir $popWord optimalBacktrack:$optimalBacktrack naiveBacktrack:$naiveBacktrack recursive calls:$countMe\n\n";
              &quickprinttofile();
              $countprint = 1;
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

        #%touchingWordsForBackTrack =(); #uncomment to stop optimal recursion?

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

sub FindLetterPosition()
{
#FindLetterPosition that we are at in @nextLetterPositionsOnBoard
#input: x , y pos @nextLetterPositionsOnBoard
#output:  $letterPosition the index we are at in
#the last x y pos after we have backtracked  and the coresponding $letterPosition
#NOT used in recursive routines. used in loop routines

my $x = $_[0];
my $y = $_[1];
my $letterPosition = 0;

until (( $nextLetterPositionsOnBoard[$letterPosition]->{x} == $x ) and ( $nextLetterPositionsOnBoard[$letterPosition]->{y} == $y ))
          {$letterPosition++}

return ($letterPosition);
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
        if ($letterList[0] eq $padsEitherSide) {@letterList = (A..Z)} #replace $padsEitherSide with (A..Z)
        else { if (scalar @letterList == 0) { return (); } }#no possible letters here, return an empty list of words
        $regexpstring = $regexpstring . '[' . join('' , @letterList) . ']';
        }

# ($wordsOfLengthString[$wordLength] =~ /$regexpstring/g) returns all possible words
#look for words already used and ignore using map!
#@possibleWords = map( { if ( $wordsThatAreInserted{$_} == 0 ) {$_} else {()} }   ($wordsOfLengthString[$wordLength] =~ /$regexpstring/g) );
#return @possibleWords; # speed up by direct output!
return map( { if ( $wordsThatAreInserted{$_} == 0 ) {$_} else {()} }   ($wordsOfLengthString[$wordLength] =~ /$regexpstring/g) );

#original non regex version
#******************************************
#sped up by just adding all possible words to a hash and incrimenting each time it shows.
#At the end if a word was counted less than the length of the word,
#then it is not a possible word
#*******************************

foreach my $referenceLetterList (@letterLists) #for each letter's position
         {
         my $aWordExistsForThisLetterPosition = 0; #assume not
         $letterPosition++;
         @letterList = @{$referenceLetterList};
         #print "@letterList\n";
         if (scalar @letterList == 0) { #no possible letters were found to cross at this position in the word, return nothing. this is required so we can pass a failed crossing word on
              return ();
              }

         #no crossing word at this letter pos (pads on either side)
         if ($letterList[0] eq $padsEitherSide) #note that this comparison denotes that there are pads on either side and THAT is why there are no letters and THAT is why we dont return a fail (empty word list)
              {
              $adjustableWordLength = $adjustableWordLength- 1; # this is here so we can eliminate wasteful code commented out below. If a letter position has no letters, then ANY letter is possible, so ignore it in the hash count
              #At the end if a word was counted less than the length of the word, then it is not a possible word

              # @letterList == ($unoccupied) therefore there was no crossing word and any letter might fit. use all $wordsOfLengthString[$wordLength]
              #@wordsFromLetters = ($wordsOfLengthString[$wordLength] =~ /.{$wordLength},/g);
              #we need to mark all possible words of this size as possible words as there is bno realling crossing word here, but words exist for this crossing space
              @wordsFromLetters = split(',' , $wordsOfLengthString[$wordLength]);
              #print "@wordsFromLetters\n\n";
              #foreach $localWord (@wordsFromLetters)
              #            {
              #            $possibleWordsCount{$localWord}++;
              #            $aWordExistsForThisLetterPosition = 1;
              #            }
              next;
              }
         #possible crossing letters at this letter pos
         #if (@letterList != ())
              {
              foreach my $letter (@letterList) #build possible word list based on word length and letter's position and possible letters here
                  {
                  @wordsFromLetters = keys %{$wordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$letterPosition]};
                  foreach $localWord (@wordsFromLetters)
                          {
                          $possibleWordsCount{$localWord}++;
                          $aWordExistsForThisLetterPosition = 1;
                          }
                  }
              }
         #no crossing letters at this letter pos
         if ($aWordExistsForThisLetterPosition == 0) {return ()} #no words are possible!
         }

#calculate  @possibleWords based on if each letter found was in this word. $possibleWordsCount{$localWord} > $wordLength
#if word count is < $wordLength then not all letters matched!
foreach $localWord (keys %possibleWordsCount) {
        if ($possibleWordsCount{$localWord} >= $adjustableWordLength)
             {
             if ( $wordsThatAreInserted{$localWord} == 0 ) # do not add words that are already used
                    {
                    push @possibleWords , $localWord;
                    }
             }
        }

return @possibleWords;
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

sub blankMaskOnBoard()
{
my $wordNumber = $_[0];
my $wordDir = $_[1];
my $mask = $allMasksOnBoard[$wordNumber][$wordDir];

$mask =~ s/./$unoccupied/g; # fill mask with $unoccupied
&placeMaskOnBoard($wordNumber , $wordDir , $mask);
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

sub outsideCrossword {
my $x = $_[0];
my $y = $_[1];
if ( ($x >= $in{width} ) || ($y >= $in{height} ) ) {return 1}
if ( ($x < 0) || ($y < 0) ) {return 1}
return 0;
};

sub quickprinttofile {
my ($x , $y);
my $line;

open (DATA, ">quickprint.txt");
# or die("Could not open file $!");
#my @lines = <DATA>;

#sleep 1;

print DATA "\n";
print DATA "Time: " , time - $timeForCrossword; #print time to create crosword
print DATA "\n";
print DATA "Loops: " , $countMe; #print time to create crosword
print DATA "\n";
print DATA "Sec per Loop: " , (time - $timeForCrossword) / $countMe; #print time to create crosword
print DATA "\n";
print DATA "Loops per Sec: " , $countMe / (time + 1 - $timeForCrossword); #print time to create crosword
print DATA "\n";

for ($y = 0 ; $y < $in{height} ; $y++)
      {
      for ($x = 0 ; $x < $in{width} ; $x++)
            {
            my $t = &GetXY($x,$y);
            #if ($t eq $padChar) {$t = "\x{2588}"};
            #if ($t eq $padChar) {$t = "\N{U+2588}"};
            $line = "$line$t";
            #$line = "$line$puzzle[$x][$y]->{Letter}";
            }
      print DATA $line;
      print DATA "\n";
      $line = '';
      }

for (my $wordNumber = 1 ; $wordNumber < 300 ; $wordNumber++)
      {
      for (my $dir = 0 ; $dir < 2 ; $dir++)
            {
            my $word = $allMasksOnBoard[$wordNumber][$dir];
            if ($word ne undef)
                 {
                 print DATA "$wordNumber $dir: $word \n"
                 }
            }
      }

print DATA "\n";
print DATA "Time: " , time - $timeForCrossword; #print time to create crosword
print DATA "\n";
print DATA "Loops: " , $countMe; #print time to create crosword
print DATA "\n";
print DATA "Sec per Loop: " , (time - $timeForCrossword) / $countMe; #print time to create crosword
print DATA "\n";
print DATA "Loops per Sec: " , $countMe / (time + 1 - $timeForCrossword); #print time to create crosword
print DATA "\n\n";

close (DATA);
};

sub getNextPossibleLetters {
#ony run when reading / loading word list
#input $_[0] mask of word ; eg COoo
#output return list of possible next letters
my $mask = $_[0];

return keys %{$linearWordSearch{$mask}};  #return possible next letters

#note not much faster than getNextPossibleLettersOld. Just simpler.
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
my $dir;
my $wordLetterPositions;

$temp = "<table cellspacing='0' cellpadding='0' CLASS='tableclass'>";
for ($y = 0; $y < $in{height}; $y++)
        {
        $temp .= "<tr>";
                for ($x = 0; $x < $in{width}; $x++)
                      {
                      print "$x, $y , $in{width}\n";
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

sub findStartOfWord()
{
#input x , y pos and direction
#output the x , y position of the start of word based on the @puzzle grid
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $count;

#back up to location of start of word
until ( ($puzzle[$x][$y]->{Letter} =~ /$padChar/)  or &outsideCrossword($x,$y) )
         {
         $x = $x - ($OppositeDirection[$dir]);
         $y = $y - $dir;
         }
#get back to start of word as we have gone too far!
$x = $x + ($OppositeDirection[$dir]);
$y = $y + $dir;
return ($x, $y);
}

sub possibleWordSize ()
{
#input x , y pos and direction. Note it might be in middle of word
#output the size of word that will fit from start of word to the next pad char or the edge or xword. based on the @puzzle grid
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $count;

if (&outsideCrossword($x,$y)) {return 0}
if ($puzzle[$x][$y]->{Letter} eq $padChar) {return 0} #no word length possible on a pad
($x,$y) = &findStartOfWord($x,$y,$dir);
# count forward till pad char (last possible word letter)
until ( ($puzzle[$x][$y]->{Letter} =~ /$padChar/)  or &outsideCrossword($x,$y) )
         {
         $x = $x + ($OppositeDirection[$dir]);
         $y = $y + $dir;
         $count++;
         }
return $count;
}

sub cgierr
{
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.

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
            $space = " " x (20 - length($env));
            print "$env$space: $ENV{$env}\n";
            }
print "\n</PRE>";
exit -1;
};