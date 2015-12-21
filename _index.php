<!DOCTYPE HTML PUBLIC "-//SoftQuad Software//DTD HoTMetaL PRO 6.0::19990601::extensions to HTML 4.0//EN" "hmpro6.dtd">
<HTML>
  <HEAD>

  <META NAME="KEYWORDS" CONTENT="infinite , instant , unlimited , crossword , cross, word, generator , puzzle , script , crosswords, printable">
<META NAME="DESCRIPTION" CONTENT="Infinite Crossword Puzzle Generator Script to create Crosswords for prining or saving for use in your web browser">


         <TITLE>Crossword Puzzle Generator by Emogic.com</TITLE>
  </HEAD>
  <BODY BACKGROUND="crossword.gif">
         <CENTER>
                <TABLE CELLPADDING="0" CELLSPACING="0" BGCOLOR="#FFFFFF">
                  <TR>
                         <TD></TD>
                  </TR>
                </TABLE>
                <TABLE CELLPADDING="0" CELLSPACING="1" BGCOLOR="#000000">
                  <TR>
                         <TD>
                                <TABLE CELLPADDING="5" CELLSPACING="0" BGCOLOR="#FFFFFF">
                                  <TR>
                                         <TD>
                                                <Center><H3>Crossword Puzzles made by Emogics Crossword Puzzle Generator</H3></center>
                                                <CENTER>
<p>
<a href="/cgi/crosswords/">Create a new Crossword Puzzle</a>
</p>

<?php
$myarray = array();

$dir="./"; // Directory where files are stored

if ($dir_list = opendir($dir))
        {
        while(($filename = readdir($dir_list)) !== false)
                {
                if ($filename != "." && $filename != ".." && $filename != "index.php")
                #if ($filename != "." && $filename != ".." && $filename != "index.php")
                #if (strpos($filename , "html"))
                        {
                        $myarray[] = $filename;
                        }
                }
        closedir($dir_list);
        }

sort($myarray);

foreach ($myarray as $key => $val)
        {

    ?>

    <a href="<?php echo $val; ?>/" target="_self"><?php echo $val;?></a> ,
    <?php

        }

?>

                                                </CENTER>
                                                <P></P> </TD>
                                  </TR>
                                </TABLE></TD>
                  </TR>
                </TABLE>
                <TABLE CELLPADDING="0" CELLSPACING="0" BGCOLOR="#FFFFFF">
                  <TR>
                         <TD> </TD>
                  </TR>
                </TABLE></CENTER> </BODY>
</HTML>