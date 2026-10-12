#!/usr/bin/perl
# Save a manually edited interface config file

require './wireguard-lib.pl';
&error_setup($text{'config_err'});
&ReadParse();

my $name = $in{'iface'};
&load_iface_or_error($name);

my $data = $in{'config'};
$data =~ s/\r//g;
$data .= "\n" if ($data !~ /\n\z/);
my ($conf, $err) = &parse_import($name, $data, 1);
&error(&html_escape($err)) if ($err);

&snapshot_conf($name);
&write_conf_text(&iface_file($name), $data);
&webmin_log('modify', 'iface', $name);

if ($in{'apply'} && &get_wg_status()->{$name}) {
	$err = &iface_action($name, 'restart');
	&error(&text('err_apply', &html_escape($err))) if ($err);
	}
&redirect("view_iface.cgi?iface=".&urlize($name));
