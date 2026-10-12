#!/usr/bin/perl
# Backup, restore and saved copies of interface configs

require './wireguard-lib.pl';
&ReadParse();

&ui_print_header(undef, $text{'backup_title'}, "");

# Full backup
print &ui_form_start("download_backup.cgi", "post");
print &ui_table_start($text{'backup_full'}, "width=100%", 2);
print &ui_table_row(undef, "$text{'backup_fulldesc'}<br><b>$text{'backup_warn'}</b>", 2);
print &ui_table_end();
print &ui_form_end([ [ undef, $text{'backup_download'} ] ]);

# Restore from a file
print &ui_form_start("restore_backup.cgi", "form-data");
print &ui_table_start($text{'backup_restore'}, "width=100%", 2);
print &ui_table_row($text{'backup_file'}, &ui_upload("file", 40));
print &ui_table_row(&hlink($text{'backup_apply'}, 'backup_apply'),
		    &ui_yesno_radio("apply", 0));
print &ui_table_row(undef, "<b>$text{'backup_trust'}</b>", 2);
print &ui_table_end();
print &ui_form_end([ [ undef, $text{'backup_restore_btn'} ] ]);

# Saved copies
print &ui_hr();
print "<h3>$text{'backup_snaps'}</h3>\n";
my $keep = &backup_keep();
print $keep ? &text('backup_snapsdesc', $keep) : $text{'backup_snapsoff'}, "<p>\n";
my %exists = map { $_, 1 } &list_interfaces();
my @rows;
foreach my $n (&list_snapshot_ifaces()) {
	foreach my $s (&list_snapshots($n)) {
		my $q = "iface=".&urlize($n)."&ts=$s->{'ts'}";
		push(@rows, [ &html_escape($n).($exists{$n} ? "" : " ($text{'backup_deleted'})"),
			      &make_date($s->{'ts'}),
			      &nice_size($s->{'size'}),
			      &ui_link("snapshot_action.cgi?$q&act=download", $text{'backup_dl'})." | ".
			      &ui_link("snapshot_action.cgi?$q&act=restore", $text{'backup_rest'})." | ".
			      &ui_link("snapshot_action.cgi?$q&act=delete", $text{'backup_del'}) ]);
		}
	}
if (@rows) {
	print &ui_columns_start([ $text{'iface_name'}, $text{'backup_date'},
				  $text{'backup_size'}, "" ]);
	print &ui_columns_row($_) foreach (@rows);
	print &ui_columns_end();
	}
else {
	print "<b>$text{'backup_nosnaps'}</b><p>\n";
	}

&ui_print_footer("", $text{'index_return'});
