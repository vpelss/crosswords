Emogic's Crossword Generation Algorithm 

My web based Crossword Generator is operational at http://www.emogic.com/cgi/crosswords/
It is intended more as a tool to study the various ways that algorithms can generate crossword puzzles and the differences between them.
It is not intended to generate New York Times quality puzzles. 

See: "Design and Implementation of Crossword Compilation Programs Using Serial Approaches" (CCP) http://thesis.cambon.dk/ for many of the concepts mentioned in this text. If you want to create your own crossword generator script,it is a great place to start. It can be unclear in many areas, but still has plenty of good ideas. That site has sample code in C. There are a few logical errors on his site based on assumptions. one big one is that a letter search is as good (or equivalent) to a word search. In a sense it is, but not when it comes to the time required to generate a crossword. 

Please use the 'Contact Us' link at the bottom if you found this useful or would like to share a thought.

Why PERL?

PERL is not known for it's speed. It also has a higher memory overhead for variable management. But it does have a few benefits. Regular expressions are powerful and fast. Hash variables (associative array) allow for an easy way to eliminate duplicate values and make it easy to search and look-up values.

PERL is ubiquitous. PERL is elegant. PERL is, in my opinion, organic. I just like PERL.

My new Crossword Source Code is at:
https://github.com/vpelss/crosswords
The word lists are not included. A wonderful one is at  www.otsys.com/clue but it must be modified to work with my code.
My code is commented. But I make no apologies if it makes no sense to you. 
It is always being modified and updated. 
If I am in the middle of a big upgrade, the code may not work.
No free support will be given.
If you have suggestions, please use the "Contact Us" link.

You can download the code for my old British style Crossword Generator at https://www.emogic.com/store/free_crossword_script. No free support will be given.

Some things I have learned

1. The bigger the word database the better.
2. Single letter searches are not the answer as there are too many combinations. For each lay of a letter you only check at most two words with the letter in common. So even with the fast calculation time for each letter, all the recursion adds up. Complete word searches (Laying a word and simultaneously checking that all the crossing words will have a possible word) although much slower, has fewer recursive calls. On most of my test scenarios, laying words was faster. Another way of stating the benefit of laying words is that a single random word replacement searches the puzzle space quicker. For example, when laying the first letter, if that letter will never result in a valid puzzle, we may not know until millions of recursions have passed. We discover mistakes faster by laying whole words.
3. Each time you lay a word, you must ensure that all it's crossing word positions will be able to fit a word. If not, you will preform too many recursions. The code is more complex, but it is worth it.
4. Your path algorithm for laying words (the order in which you lay words) must ensure that each following word in your path crosses the previous one. This helps reduce wasted recursions. A case of an inefficient recursion path would be trying to lay all across words, then checking if the down words are valid.
5. Optimal (optimized), not naive, (see CCP) backtracks help a lot (x100 speed increases or more in some cases).
6. Recursively designed routines, although not required, seem more suitable (logical) for this sort of program.

The puzzle space is immense.
The puzzle solution space is minuscule
Therefore simple recursive and random attempts are unlikely to work in a timely manner on their own.
We need to prune the search space using choice forward paths optimal backtracks.

Crossword Puzzle Grid Template Design (empty)

I chose a simple text design.

The grid templates are text files containing rows made up of 'o' and 'x'.
'x' = black squares
'o' = empty squares
The x and o were chosen as they are the same size and this gives an easily visual representation of the actual grid in notepad.

In the script they are retained as such, and do not conflict, as the inserted letters will always be capital letters.
The main array will be in the form of $puzzle[x][y]->{Letter}, but we have MANY different ways of storing this data for quick and efficient lookups and manipulation. All these alternate storage models must be updated at the same time.

eg:
xooooo
ooooxo
ooooxo

Searches

There are many types of searches we can perform to try and determine what word or letter will fit on our crossword.

Prefix / Linear Searches : Return the next potential letters after a given series of letters
Note: This  is for a letter by letter search.

Given the prefix letters for a word, return the next possible letters.
eg: given 'boa--' found in the space for a 5 letter word, the next letter might be t or r.
This is useful only if you plan to build words from beginning to end. It will not allow for filling in random letter positions.

Method 1. For each word length I built a chain of hash references. This required that we follow the chain of hash references. It was more complex but it was fast. 
$nextLetter[numberOfLettersInWord] would point to a list of hashes where the keys were possible first letters. So a "keys %nextLetter[5]" would return all the first letters of possible 5 letter words. If we chose the letter 'b', and referenced $nextLetter[5]{b} we would get a list of hash references to all the potential 2nd letters of 5 letter words that start with 'b'. etc...

*Method 2. Then I decided that it was simpler to implement and almost as fast to just use masks using prefixes. That would eliminate the need to supply the word length (as the mask is the right length). And no code to navigate a  chain of hashes was necessary.
$linearWordSearch{CAo} returned ( ${'T'} , ${'R'} , ${'B'} , ${'N'} )
I did not return a list of letters. I return a list of keys, which were the letters. This simplified the list creation ensuring there are no duplicate letters
@letters = keys %{$linearWordSearch{$mask}};
Note: the mask must be a prefix mask only. ie: HIGoooooo
It is 1.5 times slower than the old way.
Memory storage is about the same.

Mask Searches : @words = &WordsFromMask($mask) $mask = ‘GOoD’ :  Return a list of potential words for a given mask

Method 1. For a given mask (eg GOoD), cycle through all the letters given. For each letter given, return a list (built before) of all words, the same length as the mask, that have that letter in that position. Do that for all all letters that we have in the mask. Then we compare all the lists and keep the words that exist in all the lists. 
It was complex, and was not very fast as we had to repeatedly compare potentially large lists of words.
It's memory use was average to high as a  word string was stored multiple times, at least as many times as letters in the word. Eg: DOG was stored 3 times, once for each letter.

*Method 2. Words of Length String. For each word length we have created a precompiled, large comma delimited string consisting of all the words of that length. We use regular expressions to search that string for the mask and return the list of words.
The memory storage is as efficient as one could hope for. eg DOG is only stored once in the comma delimited words of 3 letter string.
The speed is surprisingly fast for searching long strings.
PERL rocks!

my $tempMask = $mask;
$tempMask =~ s/$unoccupied/\./g; #make a mask of 'GO$unoccupiedT' into 'GO.T' for the regexp (in my code $unoccupied is = o)
my $wordLength = length($tempMask);
@word_list = ($WordsOfLengthString[$wordLength] =~ /($tempMask),/g);

Method 3. Binary Mask. For each word we build a binary mask. Then for each mask we create a list of words that belong to that mask.
Eg: CAT -> CAT , CAo , CoT , Coo , oAT , etc
In theory it should be very fast. But it is only slightly faster than the Words of Length String word search in some cases. 
Copying or accessing the list takes the majority of the time and therefore is not much faster for cases where the list returned will be large. Small returned lists are faster as the Method 2 still needs to search the complete comma delimited string. 
So smaller returned word lists will show a speed improvement with this method.
However, this method uses large amounts of memory as longer words cause exponential memory growth.
It also takes a long time to build the database as we need to create many (grows exponentially as the word is longer) binary masks (and associated word lists) for every word in the dictionary. 

Possible words from letter lists Search (meta search) : choosing words that fit based on the crossing words.

A routine that takes a list of possible letters (calculated and based on all the crossing word masks) for each position in a word. 
It's output is a list of words that can be made with said letters.
@words = &WordsFromLetterLists(['C','D','F','T','Z'] , ['E','R','T','Y','O'] , ['T','R','E','W','Q','Z']);
Used if we check all possible letters at the same word position of crossing words. Then we can find the possible perpendicular words that are possible for this spot
Obviously it takes a lot of processing time. We must first search for possible letters in our word for all the crossing words.

----o---
----o---
----o---

Even though this can take up to 250 times longer than a simple mask word search (letting a simple recursive routine figure out the errors), and 833 times slower than the letter search it is faster on many types of grids as it looks at blocks of letters, not just crossing words. Therefore it notices errors sooner and avoids a lot of inefficient blind recursions. 

Note: It really shines if your walking/search path ensures that each following word crosses the previous one(s).

Optimum Backtrack for Word by Word Builds

By adding an optimum backtrack check and routine for this search, I have improved the generation time by a factor of 2500 times or more in "some" cases. If a word attempt fails, I make a list of the crossing word positions and the adjacent words positions (above, below or left/right). Those are the words that influence the word positions that failed. Then I backtrack until I hit one of the word positions in that list. You must stop on the first one encountered or you risk loosing possible puzzle solutions.

Grids that do not seem to benefit are the Double Word Grids with 100% interlock. This makes sense as all or most crossing words affect the word you are trying to solve for.

eg:
Letter Search - letter by letter routine : 0.00006 sec per call. But most recursions
Word Search Mask: 0.0002 sec per call. Many recursions.
Word Search Meta : 0.05 sec per call. Less recursions.
Word Search Meta with optimum backtrack: 0.09 sec per call. Potenially fewest recursions.

Data Structures

%WordListBy_WordLength_Letter_LetterPosition
No longer used: I use @WordsOfLengthString, masks and regex
set $WordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($letter)][$LetterPosition]{$Word} = 1
@words = keys %{$WordListBy_WordLength_Letter_LetterPosition[$wordLength][ord($Letter)][$LetterPosition]}
a hash, instead of a list, is used so we don't have duplicate words

%linearWordSearch 
No longer used: letter by letter
very fast for finding the next possible letters in a word
$linearWordSearch{mask}{key1 , key2} and it will return a list of keys (so there are no duplicates) representing the next possible letters.
@letters = keys %{$linearWordSearch{$mask}};
mask must be a prefix mask ie: TOOLooooo

@WordsOfLengthString
$WordsOfLengthString[$wordLength] = "$WordsOfLengthString[$wordLength]$Word,"; #build a comma delimited string of each possible word length
@WordsFromLetters = split (',' , $WordsOfLengthString[$wordLength]);
$tempMask = $mask;
$tempMask =~ s/$unoccupied/\./g; #make a mask of 'GO$unoccupiedT' into 'GO.T' for the regexp
$wordLength = length($tempMask);
@word_list = ($WordsOfLengthString[$wordLength] =~ /($tempMask),/g);

Our puzzle data structures use both word storage structures and letter storage structures.
Both are used at same time as both can be beneficial in different situations.

@puzzle : letter centric
the puzzle with the words inserted. array[][] returns a hash as we may want to store more data than just the cell letter in the future.  
$puzzle[$x][$y]->{Letter}

@allMasksOnBoard – word centric
all words on board whether complete or not 
$allMasksOnBoard[word number][dir 0=across 1=down] many will be undef
1 is the first word number

@LetterPositionsOfWord and @ThisSquareBelongsTowordNumber map word numbers to cell positions and vice versa.

@LetterPositionsOfWord
$LetterPositions[word #][dir] an array of all the word letter positions [[x,y],[x,y]....]
$LetterPositions[$numberCount][$Dir] = [@TempLetterPositions]; #an anonymous array reference of $x,$y pairs of all letters in the word
@WordLetterPositions = @{$LetterPositions[$wordNumber][$Dir]}
Can be used to find all crossing words fast with @ThisSquareBelongsTowordNumber and using the other $dir

@ThisSquareBelongsToWordNumber
$ThisSquareBelongsToWordNumber[x][y][dir] returns the word number this square belongs too
It can be used to find the crossing word number
$wordNumber = $ThisSquareBelongsToWordNumber[$x][$y][$dir]
$crossingwordNumber = $ThisSquareBelongsToWordNumber[$x][$y][not $dir]

@PositionInWord
$PositionInWord[x][y][dir] returns the pos of letter in the word this square belongs to starting at 0
$NthLetterPosition = $PositionInWord[$x][$y][$dir]

@NextWordPositionsOnBoard
all words position on board used for cycling through word placements, etc
 [{wordNumber => $wordNumber, Dir => $Dir},{},{}...]
$wordNumber = $NextWordPositionsOnBoard[index]{wordNumber} 
$dir = $NextWordPositionsOnBoard[index]{Dir}
recommend push and pop when using recursive routines

@nextLetterPositionsOnBoard
Not used: letter by letter search
all letter position on board used for cycling through letter placements, etc
[{x => $x, y => $y} , , ]
$x = $nextLetterPositionsOnBoard[index]{x} 
$y = $NextWordPositionsOnBoard[index]{y}
recommend push and pop when using recursive routines

%wordsThatAreInserted
$wordsThatAreInserted{word} = 1 or undef
helps prevent duplicates on the board

%wordListByMask
@words = keys $WordListByMask{oYo} 
created by taking each word, then creating a binary mask for the word and
$WordListByMask{ooRo}{WORD}=1
$WordListByMask{WoRo}{WORD}=1 etc
exponentially huge database but very fast search for words fitting a mask or pattern

%mostFrequentLetters
Not used: letter by letter search
used as @{ $mostFrequentLetters{$wordLength}{$letterPos} }
contains an ordered list of the possible letters at {$wordLength}{$letterPos} and ordered from less frequent to most frequent

@letterFrequency = (E,T,A,O,I,N,S,R,H,D,L,U,C,M,F,Y,W,G,P,B,V,K,X,Q,J,Z)
Not used: letter by letter search
a list of the most common letters first to last

%backTo{x->X , y->Y}
Not used: letter by letter search
global target used for optimal backtracking.
$backTo{x} and $backTo{y}

%wordlengths
Used to identify word lengths possible on the grid so we only load words we need.
This saves time and memory.
$wordLength{6} = 1. 

$padChar 
= 'x'

$unoccupied
 = 'o'

%clues
$clue = $clues{$word}

Word Lists example sizes

Length of word 	XW Express	Extra		Clues

2		27		30		85
3		640		788		4461
4		2273		2743		11652
5 		3468		5045		20235
6		4465		6546		24496
7		4905		7129		28296
8		4730		6636		27650
9		4130		5366		24553
10		2681		3572		24344
11		1677		2221		19815
12		823		1061		13266
13		412		614		12613
15		135		185		9597
16		0		1		2697
17		0		0		1940
18 		0		0		1018
19		0		0		930
20		0		0		3041
total		30405		42034		251578
lines		30418		53899		4325826


Walk paths for Word by Word

Flat: Horizontal words. It seems to be the fastest in a fully connected square.

Diagonal: Slow.

Switchback: Alternating horizontal and vertical word and word parts along diagonal axis. Almost as fast as flat, but no benefits.

My Cross Walk: I generated my own walk that beats the pants off the basic ones when using recursive word search algorithms that lay a word based on all the possible crossing words for that word's position.  I start with the very first word in the top right (although any start position could be used). Then I add all the crossing words to this starting word. Then I find and add all the crossing words to those words, etc. I only add a word once. This tends to backtrack very efficiently even with naive backtracking.

Walks for Letter by Letter

These walks must ensure that we are always building both the horizontal and vertical words from the first letter to the last letter. 

Optimum Backtrack : for letter by letter builds

These are tricky as the optimal backtrack is dependent on the walk we have chosen and the grid structures and pads around the failed letter.

After much thought I have simplified the many rules for choosing an optimized backtrack target to two simple rules that work with all walks and all grids. 

Since we could be using any walk (that allows us to lay words first letter to last letter):

Rule:
1. All letters in the horizontal and vertical words (up to the failed letter) can effect the failure of laying a letter, so mark it as an optimal backtrack target
2. All crossing words of both the horizontal and vertical words of the failed letter can effect the failure of laying a letter, so mark it as an optimal backtrack target
3. Remove 'shadows' by only keeping the intersection set results of rule 1 and 2

Note that # 2 can seem non intuitive. But I assure you they can. If we backtracked from the center letter (see below) and we are out of letters to lay at the 2nd row 1st column, we cannot go directly to C and try another letter. If we do, we miss words like CAR that might allow another solution in the second row that would be missed. 

Rule 3 also breaks certain grid backtracks, most notably British style crosswords. The reason is that since we are double spaced, there many shadows (rule 3) that should not be shadows. So I feel if we leave rule 3 out, the extra optimum back tracks we might miss are worth it to keep our optimum target rules simple. 

Currently, there are some cases where a walk and grid combination will break. Scenarios where the naive backtrack never hits a back track target causes these failures. eg: Letter ZigZag and 13x13_56_144

CAT
ooo
ooo

So there is no optimal backtrack in a square crossword with no black squares as per rule 1 and 2 as all squares are optimal backtrack squares.

So I am using a hash %targetLettersForBackTrack{x}{y} that will equal 1 if for all squares that follow rule 1 and 2 for a square where we cannot lay a letter or have run out of letters to try. So my optimized backtrack backtracks until it hits any of the squares in %targetLettersForBackTrack{x}{y}.

Dictionary and Clues

For huge word lists (required for big grids) a combined dictionary and clue database list is huge. 

A single database of all words and clues is very large and takes too much time to load and organize the data logically.

If we want our crossword algorithm to have quick access it must be loaded into RAM. But there are very few systems with that much RAM.

I settled on creating text files based on word lengths. 3.txt contains all 3 letter words in the dictionary. 7.txt contains all the 7 letter words.

After the crossword grid is loaded, only the required text files are loaded into a PERL array $wordsOfLengthString[$wordLength]. All the words in that array are comma delimited. Since PERL regular expression searches are amazingly fast, we can quickly search for word patterns to get the words we need to fit.

Once the words are all placed in the puzzle and we need the clues for those words. A quick way to load clues would to have a word.txt file for each word containing all the possible clues. 

jude.txt would contain:
Name in a Beatles song
Law of "Sleuth"
New Testament book
Saintly Thaddaeus
.....

This would quickly fill up all the available disk space as 250,000+ small text files take up much more disk space than the data they contain.

To save disk space I create clue text files based on the words first two letters no matter what the word size.
This takes 250,000 files and converts them into 650 files. It takes a little longer to load the clues, but it is not noticeable.

_ae.txt contains:

AEA|Thespians' org.
AEA|Thespians' org.
AEA|Thespians gp.
AEACUS|Grandfather of Achilles
AEAEA|Circe's island
...

Benchmarks

Based on the section on Double Word Squares at: http://en.wikipedia.org/wiki/Word_square
I feel my program is running well. The article states that 8 x 8 is around the largest order Double Word Square to be found using dictionary words. Considering my limited dictionary, my program can create frequently generate a 6 x 6 crossword in around 3 seconds.


Ideas/Questions

How can we create an efficient walk generator and optimal backtrack for any puzzle grid?

Could we place the backtrack and walk tasks in their own sub routines and still use recursion? Assuming we can find suitable data structures, maybe the overhead will slow it down?

Are dynamic walks (where the next walk location is chosen based on the current puzzle/grid fill) possible without missing valid puzzle combinations?

Can we further increase generation time by choosing more suitable or likely words first? 

I need to write a better clue selection routine to allow for different styles.

