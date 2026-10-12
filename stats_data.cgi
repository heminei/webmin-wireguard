#!/usr/bin/perl
# Return live counters or historical traffic as JSON

require './wireguard-lib.pl';
&ReadParse();

my $name = $in{'iface'};
&valid_iface_name($name) || &error($text{'err_name'});
-r &iface_file($name) || &error($text{'err_noiface'});

print "Content-type: application/json\n\n";

if ($in{'mode'} eq 'live') {
	my $is = &get_wg_status()->{$name};
	my %peers;
	if ($is) {
		foreach my $pub (keys %{$is->{'peers'}}) {
			my $sp = $is->{'peers'}->{$pub};
			my ($online, $ago) = &peer_runtime_info($sp);
			$peers{$pub} = { 'endpoint' => $sp->{'endpoint'},
					 'online' => $online,
					 'hs_text' => &nice_ago($ago),
					 'rx' => $sp->{'rx'}, 'tx' => $sp->{'tx'},
					 'rx_text' => &nice_size($sp->{'rx'}),
					 'tx_text' => &nice_size($sp->{'tx'}) };
			}
		}
	print &to_json({ 'up' => $is ? 1 : 0, 'peers' => \%peers });
	exit;
	}

my %ranges = ( '1h' => 3600, '24h' => 86400, '7d' => 7*86400, '30d' => 30*86400 );
my $secs = $ranges{$in{'range'}} || $ranges{'24h'};
my $pub = $in{'peer'};
$pub = undef if (!&valid_key($pub));
my $series = &get_stats_series($name, $pub, $secs, 120);
print &to_json($series);
