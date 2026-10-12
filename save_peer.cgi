#!/usr/bin/perl
# Add or update peers

require './wireguard-lib.pl';
&error_setup($text{'save_err'});
&ReadParse();

my $name = $in{'iface'};
my $conf = &load_iface_or_error($name);
my $qn = &urlize($name);

if ($in{'delete'}) {
	&redirect("action_peer.cgi?iface=$qn&delete=1&sel=".&urlize($in{'pub'}));
	exit;
	}

# Validate input
my $pname = &clean_value($in{'pname'});
length($pname) <= 60 || &error($text{'err_pname'});
my $notes = &clean_value($in{'notes'});
$in{'allowed'} =~ s/^\s+|\s+$//g;
my $count = 1;
if ($in{'new'}) {
	$count = $in{'count'};
	$count =~ /^\d+$/ && $count >= 1 && $count <= 100 || &error($text{'err_count'});
	$in{'pubkey_def'} || $count == 1 || &error($text{'err_count_key'});
	$in{'pubkey_def'} || &valid_key($in{'pubkey'}) || &error($text{'err_pubkey'});
	}
$in{'allowed'} eq '' || &valid_cidr_list($in{'allowed'}) || &error($text{'err_allowed'});

my %meta;
if (!$in{'cl_allowed_def'}) {
	&valid_cidr_list($in{'cl_allowed'}) || &error($text{'err_cl_allowed'});
	$meta{'ClientAllowedIPs'} = &clean_value($in{'cl_allowed'});
	}
if (!$in{'cl_dns_def'}) {
	&valid_dns_list($in{'cl_dns'}) || &error($text{'err_dns'});
	$meta{'ClientDNS'} = &clean_value($in{'cl_dns'});
	}
if (!$in{'cl_endpoint_def'}) {
	&valid_endpoint($in{'cl_endpoint'}) || &error($text{'err_endpoint'});
	$meta{'ClientEndpoint'} = &clean_value($in{'cl_endpoint'});
	}
if (!$in{'cl_keepalive_def'}) {
	$in{'cl_keepalive'} =~ /^\d+$/ && $in{'cl_keepalive'} <= 65535 ||
		&error($text{'err_keepalive'});
	$meta{'ClientKeepalive'} = $in{'cl_keepalive'};
	}
if (!$in{'cl_mtu_def'}) {
	$in{'cl_mtu'} =~ /^\d+$/ && $in{'cl_mtu'} >= 576 && $in{'cl_mtu'} <= 9000 ||
		&error($text{'err_mtu'});
	$meta{'ClientMTU'} = $in{'cl_mtu'};
	}

# Returns an error if any address in the list is already used by another peer
sub check_allowed_free
{
my ($conf, $list, $skip) = @_;
foreach my $o (@{$conf->{'peers'}}) {
	next if ($skip && $o eq $skip);
	my %used = map { $_, 1 } split(/\s*,\s*/, &opt_get($o, 'AllowedIPs'));
	foreach my $a (split(/\s*,\s*/, $list)) {
		&error(&text('err_inuse', &html_escape($a))) if ($used{$a});
		}
	}
}

my $newpub;
if ($in{'new'}) {
	for(my $i = 1; $i <= $count; $i++) {
		my ($priv, $pubk);
		if ($in{'pubkey_def'}) {
			$priv = &wg_genkey() || &error($text{'err_genkey'});
			$pubk = &wg_pubkey($priv) || &error($text{'err_genkey'});
			}
		else {
			$pubk = $in{'pubkey'};
			}
		&find_peer($conf, $pubk) && &error($text{'err_dupkey'});
		my $allowed = $i == 1 && $in{'allowed'} ne '' ? $in{'allowed'}
							      : &next_free_ip($conf);
		$allowed || &error($text{'err_noip'});
		&check_allowed_free($conf, $allowed);
		my $peer = { 'opts' => [], 'comments' => [], 'disabled' => 0,
			     'meta' => { %meta } };
		$peer->{'meta'}->{'Name'} = $count > 1 ? ($pname || "peer")."-$i" : $pname;
		$peer->{'meta'}->{'Notes'} = $notes;
		$peer->{'meta'}->{'PrivateKey'} = $priv;
		&opt_set($peer, 'PublicKey', $pubk);
		if ($in{'psk'}) {
			&opt_set($peer, 'PresharedKey',
				 &wg_genpsk() || &error($text{'err_genkey'}));
			}
		&opt_set($peer, 'AllowedIPs', $allowed);
		push(@{$conf->{'peers'}}, $peer);
		$newpub = $pubk;
		}
	}
else {
	my $peer = &find_peer($conf, $in{'pub'}) || &error($text{'err_nopeer'});
	$in{'allowed'} ne '' || &error($text{'err_allowed'});
	&check_allowed_free($conf, $in{'allowed'}, $peer);
	$meta{'Name'} = $pname;
	$meta{'Notes'} = $notes;
	$meta{'PrivateKey'} = $peer->{'meta'}->{'PrivateKey'};
	$peer->{'meta'} = \%meta;
	&opt_set($peer, 'AllowedIPs', $in{'allowed'});
	if (!$in{'psk'}) {
		&opt_set($peer, 'PresharedKey');
		}
	elsif (!&opt_get($peer, 'PresharedKey')) {
		&opt_set($peer, 'PresharedKey', &wg_genpsk() || &error($text{'err_genkey'}));
		}
	}

&write_wg_conf($conf);
&webmin_log($in{'new'} ? 'create' : 'modify', 'peer', $name);
my $err = &apply_if_running($name);
&error(&text('err_apply', &html_escape($err))) if ($err);

if ($in{'new'} && $count == 1) {
	&redirect("show_peer.cgi?iface=$qn&pub=".&urlize($newpub));
	}
else {
	&redirect("view_iface.cgi?iface=$qn");
	}
