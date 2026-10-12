#!/usr/bin/perl
# Stop an interface

require './wireguard-lib.pl';
&error_setup($text{'action_err'});
&ReadParse();

my $name = $in{'iface'};
&load_iface_or_error($name);
my $err = &iface_action($name, 'down');
&error("<pre>".&html_escape($err)."</pre>") if ($err);
&webmin_log('stop', 'iface', $name);
&redirect("view_iface.cgi?iface=".&urlize($name));
