#!/usr/bin/perl
# Create or update an interface

require './wireguard-lib.pl';
&error_setup($text{'save_err'});
&ReadParse();

my ($conf, $name);
if ($in{'new'}) {
	$name = $in{'name'};
	&valid_iface_name($name) || &error($text{'err_name'});
	-e &iface_file($name) && &error($text{'err_exists'});
	my $priv = &wg_genkey() || &error($text{'err_genkey'});
	$conf = { 'name' => $name, 'file' => &iface_file($name), 'peers' => [],
		  'iface' => { 'opts' => [ [ 'PrivateKey', $priv ] ],
			       'comments' => [], 'meta' => {} } };
	}
else {
	$name = $in{'iface'};
	$conf = &load_iface_or_error($name);
	}
my $sec = $conf->{'iface'};

$in{'address'} =~ s/^\s+|\s+$//g;
&valid_cidr_list($in{'address'}) || &error($text{'err_address'});
$in{'port'} =~ /^\d+$/ && $in{'port'} >= 1 && $in{'port'} <= 65535 ||
	&error($text{'err_port'});
$in{'dns'} =~ s/^\s+|\s+$//g;
$in{'dns'} eq '' || &valid_dns_list($in{'dns'}) || &error($text{'err_dns'});
if (!$in{'mtu_def'}) {
	$in{'mtu'} =~ /^\d+$/ && $in{'mtu'} >= 576 && $in{'mtu'} <= 9000 ||
		&error($text{'err_mtu'});
	}

&opt_set($sec, 'Address', split(/\s*,\s*/, $in{'address'}));
&opt_set($sec, 'ListenPort', $in{'port'});
&opt_set($sec, 'DNS', $in{'dns'});
&opt_set($sec, 'MTU', $in{'mtu_def'} ? () : $in{'mtu'});
foreach my $k ('PreUp', 'PostUp', 'PreDown', 'PostDown') {
	&opt_set($sec, $k, split(/\r?\n/, $in{lc($k)}));
	}

&write_wg_conf($conf);
&webmin_log($in{'new'} ? 'create' : 'modify', 'iface', $name);

my $err;
if (!$in{'new'} && $in{'apply'}) {
	my $st = &get_wg_status();
	$err = &iface_action($name, 'restart') if ($st->{$name});
	}
&error(&text('err_apply', &html_escape($err))) if ($err);
&redirect("view_iface.cgi?iface=".&urlize($name));
