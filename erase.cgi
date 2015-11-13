#!/usr/bin/perl

#use Fcntl qw(:flock SEEK_END);

print "Content-type: text/html\n\n";

#exists
if (not -e 'quickprint.txt')
     {
     print "File does not exist";
     exit;
     }

#locked?
if ( open(my $quickprint, "quickprint.txt") )
     {
     print "Can't open : $! $_[0]";
     exit;
     }

if ( unlink('quickprint.txt')  )
     {
     print 'Stalled crossword erased';
     }
else
    {
    print "Error trying to erase file : $! $_[0]";
    }

exit;
