#!/usr/bin/perl
# Download, restore or delete a saved copy of an interface config

require './wireguard-lib.pl';
&error_setup($text{'action_err'});
&ReadParse();

my $name = $in{'iface'};
&valid_iface_name($name) || &error($text{'err_name'});
$in{'ts'} =~ /^\d{9,11}$/ || &error($text{'err_nosnap'});
my $file = &backup_dir()."/$name/$in{'ts'}.conf";
-r $file || &error($text{'err_nosnap'});
my $when = &make_date($in{'ts'});

if ($in{'act'} eq 'download') {
	my $data = &read_file_contents($file);
	print "Content-type: text/plain\n";
	print "Content-Disposition: attachment; filename=\"$name-$in{'ts'}.conf\"\n";
	print "Content-Length: ", length($data), "\n\n";
	print $data;
	exit;
	}

if ($in{'act'} eq 'restore') {
	if (!$in{'confirm'}) {
		&ui_print_header(undef, $text{'snap_restore_title'}, "");
		print &ui_confirmation_form("snapshot_action.cgi",
			&text('snap_restore_rusure', &html_escape($name), $when),
			[ [ 'iface', $name ], [ 'ts', $in{'ts'} ], [ 'act', 'restore' ] ],
			[ [ 'confirm', $text{'snap_restore_ok'} ] ],
			&ui_checkbox("apply", 1, $text{'backup_apply'}, 0));
		&ui_print_footer("backup.cgi", $text{'backup_return'});
		exit;
		}
	my $err = &restore_snapshot($name, $in{'ts'});
	&error(&html_escape($err)) if ($err);
	&webmin_log('restore', 'snapshot', $name);
	my $st = &get_wg_status();
	if ($in{'apply'} && $st->{$name}) {
		$err = &iface_action($name, 'restart');
		&error(&text('err_apply', &html_escape($err))) if ($err);
		}
	&redirect("view_iface.cgi?iface=".&urlize($name));
	exit;
	}

if ($in{'act'} eq 'delete') {
	if (!$in{'confirm'}) {
		&ui_print_header(undef, $text{'snap_delete_title'}, "");
		print &ui_confirmation_form("snapshot_action.cgi",
			&text('snap_delete_rusure', &html_escape($name), $when),
			[ [ 'iface', $name ], [ 'ts', $in{'ts'} ], [ 'act', 'delete' ] ],
			[ [ 'confirm', $text{'delete_ok'} ] ]);
		&ui_print_footer("backup.cgi", $text{'backup_return'});
		exit;
		}
	&unlink_file($file);
	&webmin_log('delete', 'snapshot', $name);
	&redirect("backup.cgi");
	exit;
	}

&error($text{'err_noaction'});
