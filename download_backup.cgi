#!/usr/bin/perl
# Download all interface configs as a .tar.gz

require './wireguard-lib.pl';
&error_setup($text{'backup_err'});
&ReadParse();

my ($tmp, $err) = &make_backup_archive();
&error(&html_escape($err)) if ($err);

my @t = localtime(time());
my $fn = sprintf("wireguard-backup-%04d%02d%02d-%02d%02d%02d.tar.gz",
		 $t[5] + 1900, $t[4] + 1, $t[3], $t[2], $t[1], $t[0]);
my $size = -s $tmp;
&webmin_log('download', 'backup');

print "Content-type: application/gzip\n";
print "Content-Disposition: attachment; filename=\"$fn\"\n";
print "Content-Length: $size\n\n";
open(my $fh, "<", $tmp);
binmode($fh);
binmode(STDOUT);
my $buf;
print $buf while(read($fh, $buf, 65536));
close($fh);
&unlink_file($tmp);
