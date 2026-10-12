#!/usr/bin/perl
# Form for creating or editing an interface

require './wireguard-lib.pl';
&ReadParse();

my ($conf, $name);
if ($in{'new'}) {
	&ui_print_header(undef, $text{'iface_create'}, "");
	$conf = { 'iface' => { 'opts' => [ [ 'Address', '10.0.0.1/24' ],
					   [ 'ListenPort', 51820 ] ] } };
	my %taken = map { &opt_get(&read_wg_conf($_)->{'iface'}, 'ListenPort'), 1 }
			&list_interfaces();
	my $port = 51820;
	$port++ while($taken{$port});
	&opt_set($conf->{'iface'}, 'ListenPort', $port);
	}
else {
	$name = $in{'iface'};
	$conf = &load_iface_or_error($name);
	&ui_print_header(undef, &text('iface_edit', &html_escape($name)), "");
	}
my $sec = $conf->{'iface'};

print &ui_form_start("save_iface.cgi", "post");
print &ui_hidden("new", $in{'new'});
print &ui_hidden("iface", $name) if (!$in{'new'});
print &ui_table_start($text{'iface_details'}, "width=100%", 2);

print &ui_table_row(&hlink($text{'iface_name'}, 'iface_name'),
	$in{'new'} ? &ui_textbox("name", "wg0", 15) : &html_escape($name));
print &ui_table_row(&hlink($text{'iface_address'}, 'iface_address'),
	&ui_textbox("address", join(", ", &opt_get_all($sec, 'Address')), 40));
print &ui_table_row(&hlink($text{'iface_port'}, 'iface_port'),
	&ui_textbox("port", &opt_get($sec, 'ListenPort'), 6));
print &ui_table_row(&hlink($text{'iface_dns'}, 'iface_dns'),
	&ui_textbox("dns", &opt_get($sec, 'DNS'), 40));
print &ui_table_row(&hlink($text{'iface_mtu'}, 'iface_mtu'),
	&ui_opt_textbox("mtu", &opt_get($sec, 'MTU'), 6, $text{'default'}));
foreach my $k ('PreUp', 'PostUp', 'PreDown', 'PostDown') {
	print &ui_table_row(&hlink($text{'iface_'.lc($k)}, 'iface_'.lc($k)),
		&ui_textarea(lc($k), join("\n", &opt_get_all($sec, $k)), 3, 60, "off"));
	}
if (!$in{'new'}) {
	print &ui_table_row(&hlink($text{'iface_apply'}, 'iface_apply'),
		&ui_yesno_radio("apply", 1));
	}
print &ui_table_end();

if ($in{'new'}) {
	print &ui_form_end([ [ undef, $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ undef, $text{'save'} ] ]);
	}

&ui_print_footer($in{'new'} ? "" : "view_iface.cgi?iface=".&urlize($name),
		 $in{'new'} ? $text{'index_return'} : $text{'view_return'});
