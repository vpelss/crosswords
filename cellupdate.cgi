#!/usr/bin/perl

use vpvars;

#get setup variables the proper way
my $archivepath = $vpvars::archivepath;
my $archiveurl  = $vpvars::archiveurl;
my $scripturl  = $vpvars::scripturl;

eval {
      #require "vars.cgi";  #load up common variables and routines. // &cgierr
      };
warn $@ if $@;

$in{cell} = '|jK.cgi|';
$in{letter} = "L||P\i9789y";
$in{game} = " gf hjkgh  \14";
%in = &parse_form;

#$uid = $in{uid};
if ($uid eq '') {$uid='common'}

print "Content-type: text/html\n\n";
print "Content-Length: ", length(''), "\r\n\r\n"; #closes connection immediately for IE limited connection settings...
#print "$in{letter}\r\n\r\n";

$game=$in{game};
$game =~ s/[^0-9]//g; #only allow numbers
$temp = "$archivepath/$uid/$game";

$letter = $in{letter};
#if ($letter eq '.') {$letter = &};
$letter =~ s/\W//g; #block non letters
if (length($letter) > 1) {die('more than one letter')} #      {$letter = substr($letter , 0 , 1)} #filter just one letter
#$letter =~ s/[^A-Z ]/&nbsp;/g;  #block non letters and replace with &nbsp;
$letter =~ s/[^A-Z ]//g;  #block non letters and replace with blank;
$in{cell} =~ s/[^A-Z a-z 0-9 _]//g; #only letters and numbers

#$e = $in{cell};

#write cell_x_y file with letter value
open (DATA, ">$temp/$in{cell}") or die("Could not create file $temp/$in{cell}");
flock(DATA , LOCK_EX);
print DATA "$letter";
flock(DATA , LOCK_UN);
close (DATA);

#---------------

#read in all cell files
opendir(DIR, "$temp") || die "can't opendir $temp: $!";
@cellfiles = grep { /^cell/ && -f "$temp/$_" } readdir(DIR);
closedir DIR;

#compile a list of cell files and letter values and shove into a file
$outputtext = '';
foreach $cellfile (@cellfiles)
         {
         open(DATA, "<$temp/$cellfile") || die "can't opendir $cellfile: $!";
         $letter = <DATA>;
         close DATA;

         #$cellfile =~ s/\..*//;
         $outputtext = "$outputtext$cellfile=$letter|";
         }
#write output file
open (DATA, ">$temp/out.txt") or die("Could not create file $temp");
#flock(DATA , LOCK_EX);
print DATA "$outputtext";
#flock(DATA , LOCK_UN);
close (DATA);

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
