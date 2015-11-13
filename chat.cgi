#!/usr/bin/perl

use HTML::Entities;
use vpvars;

#get setup variables the proper way
my $archivepath = $vpvars::archivepath;
my $archiveurl  = $vpvars::archiveurl;
my $scripturl  = $vpvars::scripturl;

eval {
      #require "vpvars.pm";  #load up common variables and routines. // &cgierr
      };
warn $@ if $@;

print "Content-type: text/html\n\n";
#print "Content-Length: ", length(''), "\r\n\r\n"; #closes connection immediately for IE limited connection settings...

#$in{game} = 'j7576\//1235489kg jgjgjh';
%in = &parse_form;

#$uid = $in{uid};
$uid = '';
if ($uid eq '') {$uid='common'}
$game = $in{game};
$game =~ s/[^0-9]//g; #only allow numbers

$temp = "$archivepath/$uid/$game/chat.txt";

print "$temp";

if ($in{clear} == 1) #clear file
   {
   open (DATA, ">$temp") or die("Could not create file $temp");
   close (DATA);
   }

if ($in{chatline} ne '')
    {
=pod
    #limit number of lines for chatbox
    open (DATA, "<$temp") or die("Could not open file $temp");
    my @DATA = <DATA>;
    close (DATA);
    if (scalar(@DATA) > 5)
       {
       splice @DATA , 0 ,(scalar(@DATA) - 5);
       open (DATA, ">$temp") or die("Could not create file $temp");
       flock(DATA , LOCK_EX);
       print DATA @DATA;
       flock(DATA , LOCK_UN);
       close (DATA);
       }
=cut

    $name = HTML::Entities::encode($in{chatname}); #escape text to avoid code being run. Cross-site Scripting Attacks
    $line = HTML::Entities::encode($in{chatline}); #escape text to avoid code being run. Cross-site Scripting Attacks

    #Limit line length
    $strlength = 75;
    if (length($line) > $strlength)
        {$line = substr($line , 0 , $strlength)}

    $datestr = unix_to_date(time());
    $datestr = "($datestr)";
    $temp2 = "$name: <b>$line</b>&nbsp;&nbsp;&nbsp;<font size='-2'>$datestr</font>"; #add date time stamp at end of chat line

    #write archice file
    open (DATA, ">>$temp") or die("Could not create file $temp");
    flock(DATA , LOCK_EX);
    print DATA "$temp2<br>\n";
    flock(DATA , LOCK_UN);
    close (DATA);
    }

sub unix_to_date {
# --------------------------------------------------------
# This routine must take a unix time and return your date format
# A much simpler routine, just make sure your format isn't so complex that
# you can't get it back into unix time.
#
    my $time   = shift;
    my ($sec, $min, $hour, $day, $mon, $year, $dweek, $dyear, $tz) = localtime $time;
    my @months = qw!Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec!;
    $year      = $year + 1900;
    return "$day-$months[$mon]-$year $hour:$min:$sec";
}

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
