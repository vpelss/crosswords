Emogic's Crossword Generation Algorithm 

My web based Crossword Generator is operational at http://www.emogic.com/cgi/crosswords/
It is intended more as a tool to study the various ways that algorithms can generate crossword puzzles and the differences between them.
It is not intended to generate New York Times quality puzzles. 

See: "Design and Implementation of Crossword Compilation Programs Using Serial Approaches" (CCP) http://thesis.cambon.dk/ for many of the concepts mentioned in this text. If you want to create your own crossword generator script,it is a great place to start. It can be unclear in many areas, but still has plenty of good ideas. That site has sample code in C. There are a few logical errors on his site based on assumptions. one big one is that a letter search is as good (or equivalent) to a word search. In a sense it is, but not when it comes to the time required to generate a crossword. 
