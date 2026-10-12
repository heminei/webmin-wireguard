#!/usr/bin/perl
# Edit an interface config file as raw text

require './wireguard-lib.pl';
&ReadParse();

my $name = $in{'iface'};
&load_iface_or_error($name);
my $qn = &urlize($name);
my $st = &get_wg_status();

&ui_print_header(undef, &text('config_title', &html_escape($name)), "");

print &ui_form_start("save_config.cgi", "post");
print &ui_hidden("iface", $name);
print &ui_table_start($text{'config_file'}, "width=100%", 2);
print &ui_table_row(undef, $text{'config_note'}, 2);
print &ui_table_row(undef,
	&ui_textarea("config", &read_file_contents(&iface_file($name)), 25, 100, "off"), 2);
print &ui_table_row(&hlink($text{'iface_apply'}, 'iface_apply'),
	&ui_yesno_radio("apply", $st->{$name} ? 1 : 0));
print &ui_table_end();
print &ui_form_end([ [ undef, $text{'save'} ] ]);

&ui_print_footer("view_iface.cgi?iface=$qn", $text{'view_return'});
