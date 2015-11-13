#!/usr/bin/perl

print "Content-type: text/html\n\n";

#maybe not a good idea because there are a lot of dicks out there
exit;

use File::Path;
use vpvars;

#get setup variables the proper way
my $archivepath = $vpvars::archivepath;
my $archiveurl  = $vpvars::archiveurl;
my $scripturl  = $vpvars::scripturl;

eval {
#      require "vars.cgi";  #load up common variables and routines. // &cgierr
      };
warn $@ if $@;

$in{game} = "14f gdhd47252995";
#%in = &parse_form;

#$uid = $in{uid};
#$uid = 'common';
#$uid =~ s/\D//g; #only allow numbes to prevent hacking!

$game = $in{game};
$game =~ s/\D//g; #only allow numbes to prevent hacking!

$owner = $in{owner};
$owner = 'common';

=pod
if ($uid ne $owner)
     {
     print "Crossword $game failed to deleted.\n\n";
     exit;
     } #we are trying to delete someone elses games
=cut

#if (($uid ne '') and ($game ne '')) #both must be present to prevent hacking
      {
      $temp = "$archivepath/$owner/$game";
      }

rmtree($temp) or die("Crossword $game failed to deleted.");

print "Crossword $game deleted.\n\n";

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

sub cgierr
{
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.

#if ($debug == 0) {print "Epic fail...."; exit;}

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