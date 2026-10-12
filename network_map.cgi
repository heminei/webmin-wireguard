#!/usr/bin/perl
# Diagram of which peer owns which network, with overlap warnings

require './wireguard-lib.pl';
&ReadParse();

&ui_print_header(undef, $text{'map_title'}, "");

my $map = &build_network_map();
my @names = map { $_->{'name'} } @{$map->{'ifaces'}};
if (!@names) {
	print "<b>$text{'index_none'}</b><p>\n";
	&ui_print_footer("", $text{'index_return'});
	exit;
	}
my $only = (grep { $_ eq $in{'iface'} } @names)[0] || '';

print &ui_form_start("network_map.cgi", "get");
print $text{'map_show'}, " ",
      &ui_select("iface", $only, [ [ '', $text{'map_all'} ],
				   map { [ $_, $_ ] } @names ]), " ",
      &ui_submit($text{'stats_show'}), "\n";
print &ui_form_end();

# Warnings
print "<h3>$text{'map_warnings'}</h3>\n";
if (@{$map->{'warnings'}}) {
	print "<ul>\n";
	foreach my $w (@{$map->{'warnings'}}) {
		print "<li><font color=#d33>$w->{'text'}</font></li>\n";
		}
	print "</ul>\n";
	}
else {
	print "$text{'map_nowarn'}<p>\n";
	}

# Diagram
print &render_map_svg($map, $only), "<p>\n";
print "<small>$text{'map_legend'}</small><p>\n";

# Who can reach what
my $modelabel = { 'full' => $text{'map_full'}, 'split' => $text{'map_split'},
		  'custom' => $text{'map_custom'} };
foreach my $if (@{$map->{'ifaces'}}) {
	next if ($only && $if->{'name'} ne $only);
	print "<h3>", &html_escape($if->{'name'}), "</h3>\n";
	if (!@{$if->{'peers'}}) {
		print "<b>$text{'view_nopeers'}</b><p>\n";
		next;
		}
	print &ui_columns_start([ $text{'peer_name'}, $text{'map_address'},
				  $text{'map_behind'}, $text{'map_routes'},
				  $text{'map_reach'}, $text{'map_missing'} ]);
	foreach my $p (@{$if->{'peers'}}) {
		print &ui_columns_row([
			&ui_link("edit_peer.cgi?iface=".&urlize($if->{'name'}).
				 "&pub=".&urlize($p->{'pub'}), &html_escape($p->{'name'})).
				 ($p->{'disabled'} ? " ($text{'peer_disabled'})" : ""),
			&html_escape(join(", ", @{$p->{'own'}})),
			&html_escape(join(", ", @{$p->{'nets'}})) || "-",
			$modelabel->{$p->{'mode'}}.": ".
				&html_escape(join(", ", @{$p->{'client_allowed'}})),
			&html_escape(join(", ", @{$p->{'reach'}})) || "-",
			@{$p->{'missing'}} ?
				"<font color=#d33>".&html_escape(join(", ", @{$p->{'missing'}})).
				"</font>" : "-",
			]);
		}
	print &ui_columns_end();
	}
print "<small>$text{'map_note'}</small>\n";

&ui_print_footer("", $text{'index_return'});
