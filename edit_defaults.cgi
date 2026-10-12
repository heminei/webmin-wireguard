#!/usr/bin/perl
# Form for default settings of new peers and statistics

require './wireguard-lib.pl';
&ReadParse();

&ui_print_header(undef, $text{'defaults_title'}, "");

print &ui_form_start("save_defaults.cgi", "post");

print &ui_table_start($text{'defaults_peers'}, "width=100%", 2);
print &ui_table_row(&hlink($text{'peer_cl_endpoint'}, 'peer_cl_endpoint'),
	&ui_opt_textbox("endpoint", $config{'default_endpoint'}, 40,
			&text('peer_default', &get_system_hostname())));
print &ui_table_row(&hlink($text{'peer_cl_dns'}, 'peer_cl_dns'),
	&ui_textbox("dns", $config{'default_dns'}, 40));
print &ui_table_row(&hlink($text{'peer_cl_keepalive'}, 'peer_cl_keepalive'),
	&ui_opt_textbox("keepalive", $config{'default_keepalive'}, 5,
			$text{'defaults_none'}));
print &ui_table_row(&hlink($text{'peer_cl_mtu'}, 'peer_cl_mtu'),
	&ui_opt_textbox("mtu", $config{'default_mtu'}, 5, $text{'default'}));
print &ui_table_end();

print &ui_table_start($text{'defaults_stats'}, "width=100%", 2);
print &ui_table_row(&hlink($text{'defaults_collect'}, 'defaults_collect'),
	&ui_yesno_radio("collect", $config{'collect_stats'} ? 1 : 0));
print &ui_table_row(&hlink($text{'defaults_interval'}, 'defaults_interval'),
	&ui_textbox("interval", $config{'collect_interval'} || 60, 5)." ".
	$text{'defaults_seconds'});
print &ui_table_row(&hlink($text{'defaults_retention'}, 'defaults_retention'),
	&ui_textbox("retention", $config{'retention_days'} || 30, 5)." ".
	$text{'defaults_days'});
print &ui_table_end();

print &ui_table_start($text{'defaults_backups'}, "width=100%", 2);
print &ui_table_row(&hlink($text{'defaults_keep'}, 'defaults_keep'),
	&ui_textbox("keep", &backup_keep(), 5));
print &ui_table_end();

print &ui_form_end([ [ undef, $text{'save'} ] ]);

&ui_print_footer("", $text{'index_return'});
