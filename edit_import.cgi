#!/usr/bin/perl
# Form for importing a ready-made wg-quick config as a new interface

require './wireguard-lib.pl';
&ReadParse();

&ui_print_header(undef, $text{'import_title'}, "");

my %taken = map { $_, 1 } &list_interfaces();
my $n = 0;
$n++ while($taken{"wg$n"});

print &ui_form_start("save_import.cgi", "form-data");
print &ui_table_start($text{'import_details'}, "width=100%", 2);
print &ui_table_row(&hlink($text{'iface_name'}, 'iface_name'),
	&ui_textbox("name", "wg$n", 15));
print &ui_table_row(&hlink($text{'import_file'}, 'import_config'),
	&ui_upload("file", 40));
print &ui_table_row($text{'import_config'},
	&ui_textarea("config", "", 15, 70, "off"));
print &ui_table_row(&hlink($text{'import_start'}, 'import_start'),
	&ui_yesno_radio("start", 1));
if (&boot_supported()) {
	print &ui_table_row($text{'iface_boot'}, &ui_yesno_radio("boot", 1));
	}
print &ui_table_row(undef, "<b>$text{'backup_trust'}</b>", 2);
print &ui_table_end();
print &ui_form_end([ [ undef, $text{'import_btn'} ] ]);

&ui_print_footer("", $text{'index_return'});
