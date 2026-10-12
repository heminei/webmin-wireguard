#!/usr/bin/perl
# Traffic history charts

require './wireguard-lib.pl';
&ReadParse();

my @ifaces = &list_interfaces();
&ui_print_header(undef, $text{'stats_title'}, "");

if (!@ifaces) {
	print "<b>$text{'index_none'}</b><p>\n";
	&ui_print_footer("", $text{'index_return'});
	exit;
	}
if (!$config{'collect_stats'}) {
	print "<b>$text{'stats_disabled'}</b><p>\n";
	}

my $name = (grep { $_ eq $in{'iface'} } @ifaces)[0] || $ifaces[0];
my $conf = &read_wg_conf($name);
my $range = (grep { $_ eq $in{'range'} } ('1h', '24h', '7d', '30d'))[0] || '24h';
my $peer = &valid_key($in{'peer'}) ? $in{'peer'} : '';

my @peeropts = ([ '', $text{'stats_allpeers'} ]);
foreach my $p (@{$conf->{'peers'}}) {
	my $pub = &opt_get($p, 'PublicKey');
	push(@peeropts, [ $pub, $p->{'meta'}->{'Name'} || substr($pub, 0, 8) ]);
	}

print &ui_form_start("stats.cgi", "get");
print &ui_table_start($text{'stats_filter'}, undef, 2);
print &ui_table_row($text{'iface_name'},
	&ui_select("iface", $name, [ map { [ $_, $_ ] } @ifaces ]));
print &ui_table_row($text{'stats_peer'}, &ui_select("peer", $peer, \@peeropts));
print &ui_table_row($text{'stats_range'},
	&ui_select("range", $range, [ [ '1h', $text{'stats_1h'} ],
				      [ '24h', $text{'stats_24h'} ],
				      [ '7d', $text{'stats_7d'} ],
				      [ '30d', $text{'stats_30d'} ] ]));
print &ui_table_end();
print &ui_form_end([ [ undef, $text{'stats_show'} ] ]);

print "<canvas id=wg-chart width=900 height=320 ",
      "style='max-width:100%;border:1px solid #ccc;background:#fff'></canvas>\n";
my $url = "stats_data.cgi?iface=".&urlize($name)."&range=".&urlize($range).
	  ($peer ? "&peer=".&urlize($peer) : "");
print &load_script_then('wg-chart.js',
      "wgChart('wg-chart', ".&json_str($url).", {\n".
      "  rx:".&json_str($text{'stats_rx'}).", tx:".&json_str($text{'stats_tx'}).",\n".
      "  empty:".&json_str($text{'stats_nodata'})."});\n");

&ui_print_footer("", $text{'index_return'});
