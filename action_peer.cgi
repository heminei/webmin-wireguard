#!/usr/bin/perl
# Enable, disable or delete selected peers

require './wireguard-lib.pl';
&error_setup($text{'action_err'});
&ReadParse();

my $name = $in{'iface'};
my $conf = &load_iface_or_error($name);
my $qn = &urlize($name);
my @sel = grep { &valid_key($_) } split(/\0/, $in{'sel'});
@sel || &error($text{'err_nosel'});
my %sel = map { $_, 1 } @sel;
my @peers = grep { $sel{&opt_get($_, 'PublicKey')} } @{$conf->{'peers'}};
@peers || &error($text{'err_nopeer'});

if ($in{'delete'} && !$in{'confirm'}) {
	&ui_print_header(undef, $text{'pdelete_title'}, "");
	print &ui_confirmation_form("action_peer.cgi",
		&text('pdelete_rusure', scalar(@peers)),
		[ [ 'iface', $name ], [ 'delete', 1 ],
		  map { [ 'sel', $_ ] } @sel ],
		[ [ 'confirm', $text{'delete_ok'} ] ]);
	&ui_print_footer("view_iface.cgi?iface=$qn", $text{'view_return'});
	exit;
	}

if ($in{'delete'}) {
	$conf->{'peers'} = [ grep { !$sel{&opt_get($_, 'PublicKey')} }
				  @{$conf->{'peers'}} ];
	}
elsif ($in{'enable'} || $in{'disable'}) {
	foreach my $p (@peers) {
		$p->{'disabled'} = $in{'disable'} ? 1 : 0;
		}
	}
else {
	&error($text{'err_noaction'});
	}

&write_wg_conf($conf);
&webmin_log($in{'delete'} ? 'delete' : $in{'enable'} ? 'enable' : 'disable',
	    'peer', $name);
my $err = &apply_if_running($name);
&error(&text('err_apply', &html_escape($err))) if ($err);
&redirect("view_iface.cgi?iface=$qn");
