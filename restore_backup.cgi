#!/usr/bin/perl
# Restore interface configs from an uploaded backup

require './wireguard-lib.pl';
&error_setup($text{'restore_err'});
&ReadParseMime(10 * 1024 * 1024 + 4096);

my ($names, $err) = &restore_archive($in{'file'});
&error(&html_escape($err)) if ($err);
&webmin_log('restore', 'upload', join(",", @$names));

my $st = &get_wg_status();
my @msgs;
foreach my $n (@$names) {
	next if (!$in{'apply'} || !$st->{$n});
	my $e = &iface_action($n, 'restart');
	push(@msgs, &text('restore_failed', &html_escape($n), &html_escape($e))) if ($e);
	}

&ui_print_header(undef, $text{'restore_title'}, "");
print &text('restore_done', scalar(@$names)), "<p>\n<ul>\n";
print "<li>", &ui_link("view_iface.cgi?iface=".&urlize($_), &html_escape($_)), "</li>\n"
	foreach (@$names);
print "</ul>\n";
print "<font color=#d33>$_</font><br>\n" foreach (@msgs);
print "$text{'restore_norestart'}<p>\n" if (!$in{'apply'});
&ui_print_footer("backup.cgi", $text{'backup_return'});
