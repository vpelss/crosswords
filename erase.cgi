#!/usr/bin/perl

#use Fcntl qw(:flock SEEK_END);
use Fcntl

print "Content-type: text/html\n\n"; 

#exists
if (not -e 'processing.txt')
     {
     print "File does not exist";
     exit;
     }

#locked?
my $quickprint;
open($quickprint , ">>", "processing.txt")
        or die "Can't open file: $!";
flock($quickprint, LOCK_EX) 
        or print "Still running. Cannot lock file - $!\n"; 
close $quickprint;

if ( unlink('processing.txt')  )
     {
     print 'Stalled crossword erased';
     }
else
    {
    print "Error trying to erase file : $! $_[0]";
    }

#print "reached end?";
exit;
