package vpvars;

#relative to script location or full server path if microsoft
$archivepath = "../../crosswords";

#$baseurl = "http://www.emogic.com";
$baseurl = "";

#$archiveurl = "http://127.0.0.1/crosswords";
$archiveurl = "$baseurl/crosswords";

$scripturl = "$baseurl/cgi/crosswords";

$SEND_MAIL= "/usr/lib/sendmail -t";
#example: $SEND_MAIL="/usr/lib/sendmail -t";

#$SMTP_SERVER="mail.yourdomain.com";
#use SMTP_SERVER if SEND_MAIL is unavailable, BUT NOT BOTH
#example: $SMTP_SERVER="mail.yourdomain.com";

$from = "CrossWord Mailer Ver 1.0 <vpelss\@emogic.com>";
#This will be in all Email from addresses
#example $from = "Tarot Mailer Ver 1.0 <vpelss\@emogic.com>";
#THE SLASH IS MANDITORY!

$subject = "CrossWords for Friends from Emogic.com";
#email subject. Note: The script adds the visitors name will show at the end
$subject = 'I have Crosswords for you!';

1;