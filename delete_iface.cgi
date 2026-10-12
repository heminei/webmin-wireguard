#!/usr/bin/perl
# Delete an interface after confirmation

require './wireguard-lib.pl';
&error_setup($text{'action_err'});
&ReadParse();

my $name = $in{'iface'};
my $conf = &load_iface_or_error($name);
my $back = "view_iface.cgi?iface=".&urlize($name);

if (!$in{'confirm'}) {
	&ui_print_header(undef, $text{'delete_title'}, "");
	print &ui_confirmation_form("delete_iface.cgi",
		&text('delete_rusure', &html_escape($name),
		      scalar(@{$conf->{'peers'}})),
		[ [ 'iface', $name ] ],
		[ [ 'confirm', $text{'delete_ok'} ] ]);
	&ui_print_footer($back, $text{'view_return'});
	exit;
	}

my $st = &get_wg_status();
&iface_action($name, 'down') if ($st->{$name});
&iface_set_boot($name, 0) if (&boot_supported() && &iface_boot_enabled($name));
&snapshot_conf($name);
&unlink_file(&iface_file($name));
&unlink_file(&stats_file($name));
&webmin_log('delete', 'iface', $name);
&redirect("");
