#!/usr/bin/perl
# Reload peers of a running interface, or toggle start at boot

require './wireguard-lib.pl';
&error_setup($text{'action_err'});
&ReadParse();

my $name = $in{'iface'};
&load_iface_or_error($name);

my $err;
if ($in{'reload'}) {
	$err = &iface_action($name, 'reload');
	&webmin_log('reload', 'iface', $name) if (!$err);
	}
elsif ($in{'boot_on'}) {
	$err = &iface_set_boot($name, 1);
	&webmin_log('enable', 'iface', $name) if (!$err);
	}
elsif ($in{'boot_off'}) {
	$err = &iface_set_boot($name, 0);
	&webmin_log('disable', 'iface', $name) if (!$err);
	}
else {
	&error($text{'err_noaction'});
	}
&error("<pre>".&html_escape($err)."</pre>") if ($err);
&redirect("view_iface.cgi?iface=".&urlize($name));
