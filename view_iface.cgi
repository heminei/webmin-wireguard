#!/usr/bin/perl
# Show an interface, its status and its peers

require './wireguard-lib.pl';
&ReadParse();

my $name = $in{'iface'};
my $conf = &load_iface_or_error($name);
my $st = &get_wg_status();
my $is = $st->{$name};
my $qn = &urlize($name);

my @hl;
push(@hl, $is ? [ "stop.cgi?iface=$qn", $text{'view_stop'} ]
	      : [ "start.cgi?iface=$qn", $text{'view_start'} ]);
push(@hl, [ "restart.cgi?iface=$qn", $text{'view_restart'} ]) if ($is);
push(@hl, [ "delete_iface.cgi?iface=$qn", $text{'view_delete'} ]);

&ui_print_header(undef, &text('view_title', &html_escape($name)), "", undef, 0, 0, 0,
		&header_links(\@hl));

# Less common actions are normal links, as the theme only shows start, stop,
# restart and delete as header buttons
my @links = ( &ui_link("edit_iface.cgi?iface=$qn", $text{'view_edit'}),
	      &ui_link("edit_config.cgi?iface=$qn", $text{'view_editconfig'}) );
push(@links, &ui_link("action_iface.cgi?iface=$qn&reload=1", $text{'view_reload'}))
	if ($is);
if (&boot_supported()) {
	push(@links, &iface_boot_enabled($name) ?
		&ui_link("action_iface.cgi?iface=$qn&boot_off=1", $text{'view_bootoff'}) :
		&ui_link("action_iface.cgi?iface=$qn&boot_on=1", $text{'view_booton'}));
	}
print &ui_links_row(\@links);

# Interface details
print &ui_table_start($text{'view_info'}, "width=100%", 4);
print &ui_table_row($text{'iface_status'},
	$is ? "<font color=#00aa00>$text{'iface_up'}</font>"
	    : "<font color=#aa0000>$text{'iface_down'}</font>");
print &ui_table_row($text{'iface_pubkey'},
	"<tt>".&html_escape(&iface_public_key($conf) || '-')."</tt>");
print &ui_table_row($text{'iface_address'},
	&html_escape(join(", ", &opt_get_all($conf->{'iface'}, 'Address'))) || "-");
print &ui_table_row($text{'iface_port'},
	&html_escape(&opt_get($conf->{'iface'}, 'ListenPort')) || "-");
print &ui_table_row($text{'iface_dns'},
	&html_escape(&opt_get($conf->{'iface'}, 'DNS')) || "-");
print &ui_table_row(&hlink($text{'iface_boot'}, 'iface_boot'),
	&boot_supported() ? ($text{&iface_boot_enabled($name) ? 'yes' : 'no'})
			  : $text{'view_noboot'});
print &ui_table_end();

# Peers
print &ui_hr();
print "<h3>$text{'view_peers'}</h3>\n";
print &ui_link("edit_peer.cgi?iface=$qn&new=1", $text{'view_addpeer'}),"<br>\n";
if (@{$conf->{'peers'}}) {
	print &ui_form_start("action_peer.cgi", "post");
	print &ui_hidden("iface", $name);
	print "<a href='#' onclick=\"var c=document.querySelectorAll('input[name=sel]');".
	      "for(var i=0;i<c.length;i++){c[i].checked=!c[i].checked;}return false\">".
	      "$text{'view_invert'}</a>\n";
	print &ui_columns_start([ "", $text{'peer_name'}, $text{'peer_allowed'},
				  $text{'peer_endpoint'}, $text{'peer_handshake'},
				  $text{'peer_rx'}, $text{'peer_tx'},
				  $text{'peer_state'}, "" ]);
	foreach my $p (@{$conf->{'peers'}}) {
		my $pub = &opt_get($p, 'PublicKey');
		my $sp = $is ? $is->{'peers'}->{$pub} : undef;
		my ($online, $ago) = &peer_runtime_info($sp);
		my $ep = $sp ? $sp->{'endpoint'} : '';
		my $attr = "data-pub='".&html_escape($pub)."'";
		my $state = $p->{'disabled'} ? $text{'peer_disabled'} :
			    !$is ? "-" :
			    $online ? "<font color=#00aa00>$text{'peer_online'}</font>" :
				      $text{'peer_offline'};
		print &ui_columns_row([
			&ui_checkbox("sel", $pub, "", 0),
			&ui_link("edit_peer.cgi?iface=$qn&pub=".&urlize($pub),
				 &html_escape($p->{'meta'}->{'Name'} || substr($pub, 0, 8))),
			&html_escape(&opt_get($p, 'AllowedIPs')),
			"<span class=wg-ep $attr>".&html_escape($ep)."</span>",
			"<span class=wg-hs $attr>".($sp ? &nice_ago($ago) : "-")."</span>",
			"<span class=wg-rx $attr>".($sp ? &nice_size($sp->{'rx'}) : "-")."</span>",
			"<span class=wg-tx $attr>".($sp ? &nice_size($sp->{'tx'}) : "-")."</span>",
			"<span class=wg-st $attr".($p->{'disabled'} ? " data-dis=1" : "").
			  ">$state</span>",
			&ui_link("show_peer.cgi?iface=$qn&pub=".&urlize($pub),
				 $text{'peer_config'}),
			]);
		}
	print &ui_columns_end();
	print &ui_form_end([ [ "enable", $text{'peer_enable'} ],
			     [ "disable", $text{'peer_disable'} ],
			     [ "delete", $text{'peer_delete'} ] ]);
	}
else {
	print "<b>$text{'view_nopeers'}</b><p>\n";
	}

print &load_script_then('wg-live.js',
      "wgLive(".&json_str($name).", {\n".
      "  online:".&json_str($text{'peer_online'}).",\n".
      "  offline:".&json_str($text{'peer_offline'})."});\n") if ($is);

&ui_print_footer("", $text{'index_return'});
