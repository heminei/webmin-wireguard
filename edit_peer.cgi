#!/usr/bin/perl
# Form for adding or editing a peer

require './wireguard-lib.pl';
&ReadParse();

my $name = $in{'iface'};
my $conf = &load_iface_or_error($name);
my $qn = &urlize($name);
my ($peer, $pub, $m);
if ($in{'new'}) {
	&ui_print_header(undef, $text{'peer_create'}, "");
	$m = {};
	}
else {
	$pub = $in{'pub'};
	$peer = &find_peer($conf, $pub) || &error($text{'err_nopeer'});
	$m = $peer->{'meta'};
	&ui_print_header(undef, &text('peer_edit',
		&html_escape($m->{'Name'} || substr($pub, 0, 8))), "");
	}

print &ui_form_start("save_peer.cgi", "post");
print &ui_hidden("iface", $name);
print &ui_hidden("new", $in{'new'});
print &ui_hidden("pub", $pub) if (!$in{'new'});
print &ui_table_start($text{'peer_details'}, "width=100%", 2);

print &ui_table_row(&hlink($text{'peer_name'}, 'peer_name'),
	&ui_textbox("pname", $m->{'Name'}, 30));
print &ui_table_row(&hlink($text{'peer_notes'}, 'peer_notes'),
	&ui_textbox("notes", $m->{'Notes'}, 60));
if ($in{'new'}) {
	print &ui_table_row(&hlink($text{'peer_count'}, 'peer_count'),
		&ui_textbox("count", 1, 4));
	print &ui_table_row(&hlink($text{'peer_pubkey'}, 'peer_pubkey'),
		&ui_opt_textbox("pubkey", undef, 45, $text{'peer_autogen'}));
	}
else {
	print &ui_table_row(&hlink($text{'peer_pubkey'}, 'peer_pubkey'),
		"<tt>".&html_escape($pub)."</tt>");
	}
print &ui_table_row(&hlink($text{'peer_allowed'}, 'peer_allowed'),
	&ui_textbox("allowed", $in{'new'} ? &next_free_ip($conf) :
					    &opt_get($peer, 'AllowedIPs'), 40));
print &ui_table_row(&hlink($text{'peer_psk'}, 'peer_psk'),
	&ui_yesno_radio("psk", $in{'new'} ? 1 : (&opt_get($peer, 'PresharedKey') ? 1 : 0)));
print &ui_table_end();

print &ui_table_start($text{'peer_client'}, "width=100%", 2);
print &ui_table_row(&hlink($text{'peer_cl_allowed'}, 'peer_cl_allowed'),
	&ui_opt_textbox("cl_allowed", $m->{'ClientAllowedIPs'}, 40,
			&text('peer_default', join(", ", &iface_subnets($conf)))));
print &ui_table_row(&hlink($text{'peer_cl_dns'}, 'peer_cl_dns'),
	&ui_opt_textbox("cl_dns", $m->{'ClientDNS'}, 40,
			&text('peer_default', $config{'default_dns'} || '-')));
print &ui_table_row(&hlink($text{'peer_cl_endpoint'}, 'peer_cl_endpoint'),
	&ui_opt_textbox("cl_endpoint", $m->{'ClientEndpoint'}, 40,
			&text('peer_default', $config{'default_endpoint'} ||
					      &get_system_hostname())));
print &ui_table_row(&hlink($text{'peer_cl_keepalive'}, 'peer_cl_keepalive'),
	&ui_opt_textbox("cl_keepalive", $m->{'ClientKeepalive'}, 5,
			&text('peer_default', $config{'default_keepalive'} || '-')));
print &ui_table_row(&hlink($text{'peer_cl_mtu'}, 'peer_cl_mtu'),
	&ui_opt_textbox("cl_mtu", $m->{'ClientMTU'}, 5,
			&text('peer_default', $config{'default_mtu'} || '-')));
print &ui_table_end();

if ($in{'new'}) {
	print &ui_form_end([ [ undef, $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ undef, $text{'save'} ],
			     [ 'delete', $text{'peer_delete'} ] ]);
	}

if (!$in{'new'}) {
	print &ui_hr();
	print "<h3>$text{'peer_traffic'}</h3>\n";
	print "<b>$text{'stats_disabled'}</b><p>\n" if (!$config{'collect_stats'});
	print &ui_select("wg-range", "24h",
		[ [ '1h', $text{'stats_1h'} ], [ '24h', $text{'stats_24h'} ],
		  [ '7d', $text{'stats_7d'} ], [ '30d', $text{'stats_30d'} ] ],
		1, 0, 0, 0, "id=wg-range"), "<br>\n";
	print "<canvas id=wg-chart width=900 height=320 ",
	      "style='max-width:100%;border:1px solid #ccc;background:#fff'></canvas>\n";
	my $base = "stats_data.cgi?iface=$qn&peer=".&urlize($pub)."&range=";
	print &load_script_then('wg-chart.js',
	      "var sel = document.getElementById('wg-range');\n".
	      "function draw() {\n".
	      "  wgChart('wg-chart', ".&json_str($base)." + sel.value, {\n".
	      "    rx:".&json_str($text{'stats_rx'}).", tx:".&json_str($text{'stats_tx'}).",\n".
	      "    empty:".&json_str($text{'stats_nodata'})."});\n".
	      "}\n".
	      "sel.onchange = draw;\n".
	      "draw();\n");
	}

&ui_print_footer("view_iface.cgi?iface=$qn", $text{'view_return'});
