#!/usr/bin/perl
# List WireGuard interfaces

require './wireguard-lib.pl';

my $ver = &wg_version();
&ui_print_header($ver ? &text('index_version', $ver) : undef,
	$text{'index_title'}, "", undef, 1, 1);

if (my $err = &check_wireguard()) {
	&ui_print_endpage(&text('index_ecmd', $err));
	}
&ensure_collector_job();

my @ifaces = &list_interfaces();
my $st = &get_wg_status();

print &ui_links_row([ &ui_link("edit_iface.cgi?new=1", $text{'index_add'}),
		      &ui_link("edit_import.cgi", $text{'index_import'}),
		      &ui_link("network_map.cgi", $text{'index_map'}),
		      &ui_link("stats.cgi", $text{'index_stats'}),
		      &ui_link("backup.cgi", $text{'index_backup'}),
		      &ui_link("edit_defaults.cgi", $text{'index_defaults'}) ]);
if (@ifaces) {
	print &ui_columns_start([ $text{'iface_name'}, $text{'iface_status'},
				  $text{'iface_address'}, $text{'iface_port'},
				  $text{'iface_peers'}, $text{'peer_online'},
				  $text{'peer_rx'}, $text{'peer_tx'} ]);
	foreach my $n (@ifaces) {
		my $conf = &read_wg_conf($n);
		my $is = $st->{$n};
		my ($online, $rx, $tx) = (0, 0, 0);
		if ($is) {
			foreach my $sp (values %{$is->{'peers'}}) {
				my ($o) = &peer_runtime_info($sp);
				$online += $o;
				$rx += $sp->{'rx'};
				$tx += $sp->{'tx'};
				}
			}
		print &ui_columns_row([
			&ui_link("view_iface.cgi?iface=".&urlize($n),
				 &html_escape($n)),
			$is ? "<font color=#00aa00>$text{'iface_up'}</font>"
			    : "<font color=#aa0000>$text{'iface_down'}</font>",
			&html_escape(join(", ", &opt_get_all($conf->{'iface'}, 'Address'))),
			&html_escape(&opt_get($conf->{'iface'}, 'ListenPort')),
			scalar(@{$conf->{'peers'}}),
			$is ? $online : "-",
			$is ? &nice_size($rx) : "-",
			$is ? &nice_size($tx) : "-",
			]);
		}
	print &ui_columns_end();
	}
else {
	print "<b>$text{'index_none'}</b><p>\n";
	}
print &ui_links_row([ &ui_link("edit_iface.cgi?new=1", $text{'index_add'}) ]);

&ui_print_footer("/", $text{'index'});
