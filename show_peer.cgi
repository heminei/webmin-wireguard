#!/usr/bin/perl
# Show a peer's client config, QR code and download link

require './wireguard-lib.pl';
&ReadParse();

my $name = $in{'iface'};
my $conf = &load_iface_or_error($name);
my $peer = &find_peer($conf, $in{'pub'}) || &error($text{'err_nopeer'});
my $qn = &urlize($name);
my $qp = &urlize($in{'pub'});
my $pname = $peer->{'meta'}->{'Name'} || substr($in{'pub'}, 0, 8);

&ui_print_header(undef, &text('show_title', &html_escape($pname)), "");

my ($cfg, $err) = &build_client_config($conf, $peer);
if ($err) {
	print "<b>", &html_escape($err), "</b><p>\n";
	&ui_print_footer("view_iface.cgi?iface=$qn", $text{'view_return'});
	exit;
	}

print &ui_link("download_peer.cgi?iface=$qn&pub=$qp", $text{'show_download'}),
      " | ",
      &ui_link("edit_peer.cgi?iface=$qn&pub=$qp", $text{'show_edit'}), "<p>\n";

print "<table><tr><td valign=top>\n";
print "<textarea id=wg-cfg rows=20 cols=60 readonly>", &html_escape($cfg),
      "</textarea><br>\n";
print "<button type=button class='btn btn-default' style='margin-top:5px' ",
      "onclick=\"var b=this,o=b.textContent,t=document.getElementById('wg-cfg');t.select();",
      "if(navigator.clipboard){navigator.clipboard.writeText(t.value);}",
      "else{document.execCommand('copy');}",
      "b.textContent=", &html_escape(&json_str($text{'show_copied'})),
      ";setTimeout(function(){b.textContent=o;},1500);\">",
      "$text{'show_copy'}</button>\n";
print "</td><td valign=top style='padding-left:20px'>\n";

print "<div id=wg-qr style='width:300px;height:300px;background:#fff;color:#000'></div>\n";
print "</td></tr></table>\n";
print &load_script_then('qrcode.js',
      "var el = document.getElementById('wg-qr');\n".
      "try {\n".
      "  var qr = qrcode(0, 'M');\n".
      "  qr.addData(document.getElementById('wg-cfg').value);\n".
      "  qr.make();\n".
      "  el.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 16, scalable: true });\n".
      "} catch (e) {\n".
      "  el.textContent = ".&json_str($text{'show_noqr'}).";\n".
      "}\n");

&ui_print_footer("view_iface.cgi?iface=$qn", $text{'view_return'});
