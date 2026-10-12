#!/usr/bin/perl
# Restart an interface so that saved changes take effect

require './wireguard-lib.pl';
&error_setup($text{'action_err'});
&ReadParse();

my $name = $in{'iface'};
&load_iface_or_error($name);
my $err = &iface_action($name, 'restart');
&error("<pre>".&html_escape($err)."</pre>") if ($err);
&webmin_log('restart', 'iface', $name);
&redirect("view_iface.cgi?iface=".&urlize($name));
