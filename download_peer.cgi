#!/usr/bin/perl
# Download a peer's client config as a .conf file

require './wireguard-lib.pl';
&ReadParse();

my $conf = &load_iface_or_error($in{'iface'});
my $peer = &find_peer($conf, $in{'pub'}) || &error($text{'err_nopeer'});
my ($cfg, $err) = &build_client_config($conf, $peer);
&error(&html_escape($err)) if ($err);

my $fn = &peer_filename($peer);
print "Content-type: text/plain\n";
print "Content-Disposition: attachment; filename=\"$fn\"\n";
print "Content-Length: ", length($cfg), "\n\n";
print $cfg;
