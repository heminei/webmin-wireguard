#!/usr/bin/perl
# Create an interface from an uploaded or pasted wg-quick config

require './wireguard-lib.pl';
&error_setup($text{'import_err'});
&ReadParseMime(70000);

my $name = $in{'name'};
&valid_iface_name($name) || &error($text{'err_name'});
-e &iface_file($name) && &error($text{'err_exists'});

my $data = length($in{'file'}) ? $in{'file'} : $in{'config'};
my ($conf, $err) = &parse_import($name, $data);
&error(&html_escape($err)) if ($err);

&write_wg_conf($conf);
&webmin_log('import', 'iface', $name);

if ($in{'boot'} && &boot_supported()) {
	$err = &iface_set_boot($name, 1);
	}
$err ||= &iface_action($name, 'up') if ($in{'start'});
&error(&text('err_apply', &html_escape($err))) if ($err);
&redirect("view_iface.cgi?iface=".&urlize($name));
