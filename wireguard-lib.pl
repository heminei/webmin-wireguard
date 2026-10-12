#!/usr/bin/perl
# Common functions for the WireGuard module

BEGIN { push(@INC, ".."); };
use WebminCore;
use Math::BigInt;
&init_config();

# Metadata kept as comments inside [Peer] sections, ignored by wg-quick
@peer_meta_keys = ('Name', 'Notes', 'PrivateKey', 'ClientDNS', 'ClientAllowedIPs',
		   'ClientEndpoint', 'ClientKeepalive', 'ClientMTU');
$disabled_prefix = "#DISABLED# ";
$online_seconds = 180;

############################ commands and checks ############################

sub wg_cmd { return $config{'wg_cmd'} || 'wg'; }
sub wg_quick_cmd { return $config{'wg_quick_cmd'} || 'wg-quick'; }
sub config_dir { return $config{'config_dir'} || '/etc/wireguard'; }

# wg_version()
# Returns the wireguard-tools version, or undef if it cannot be detected
sub wg_version
{
&has_command(&wg_cmd()) || return undef;
my ($out, $err);
&execute_command(&wg_cmd()." --version", undef, \$out, \$err);
return $out =~ /v(\d+(?:\.\d+)+)/ ? $1 : undef;
}

# header_links(&[ [url, text], .. ])
# Returns HTML for the right side of a page header, shown as buttons by themes
sub header_links
{
my ($links) = @_;
return join("<br>\n", map { &ui_link($_->[0], $_->[1]) } @$links);
}

# check_wireguard()
# Returns an error message if the WireGuard tools are missing, undef otherwise
sub check_wireguard
{
&has_command(&wg_cmd()) || return &text('err_nocmd', &wg_cmd());
&has_command(&wg_quick_cmd()) || return &text('err_nocmd', &wg_quick_cmd());
return undef;
}

############################ validation ############################

sub valid_iface_name
{
return $_[0] =~ /^[a-zA-Z0-9_=+.][a-zA-Z0-9_=+.-]{0,14}$/ ? 1 : 0;
}

sub valid_key
{
return $_[0] =~ /^[A-Za-z0-9+\/]{43}=$/ ? 1 : 0;
}

sub valid_cidr
{
my ($c) = @_;
if ($c =~ /^(\d+)\.(\d+)\.(\d+)\.(\d+)\/(\d+)$/) {
	return ($1 <= 255 && $2 <= 255 && $3 <= 255 && $4 <= 255 && $5 <= 32);
	}
if ($c =~ /^([0-9a-fA-F:]+)\/(\d+)$/) {
	my ($addr, $len) = ($1, $2);
	return ($addr =~ /:/ && $len <= 128) ? 1 : 0;
	}
return 0;
}

# valid_cidr_list(string)
# Returns 1 if the string is a comma-separated list of CIDR addresses
sub valid_cidr_list
{
my ($str) = @_;
my @l = split(/\s*,\s*/, $str);
return 0 if (!@l);
foreach my $c (@l) {
	return 0 if (!&valid_cidr($c));
	}
return 1;
}

# valid_dns_list(string)
# Returns 1 if the string is a comma-separated list of IPs or hostnames
sub valid_dns_list
{
my ($str) = @_;
my @l = split(/\s*,\s*/, $str);
return 0 if (!@l);
foreach my $d (@l) {
	return 0 if ($d !~ /^[A-Za-z0-9.:_-]+$/);
	}
return 1;
}

sub valid_endpoint
{
return $_[0] =~ /^(\[[0-9a-fA-F:]+\]|[A-Za-z0-9._-]+)(:\d{1,5})?$/ ? 1 : 0;
}

# clean_value(string)
# Strips characters that would break the line-based config format
sub clean_value
{
my ($v) = @_;
$v =~ s/[\r\n\0]+/ /g;
$v =~ s/^\s+//;
$v =~ s/\s+$//;
return $v;
}

############################ interfaces ############################

sub iface_file
{
return &config_dir()."/".$_[0].".conf";
}

# list_interfaces()
# Returns names of all configured interfaces
sub list_interfaces
{
my @rv;
opendir(my $dh, &config_dir()) || return ();
foreach my $f (sort readdir($dh)) {
	if ($f =~ /^(.+)\.conf$/ && &valid_iface_name($1)) {
		push(@rv, $1);
		}
	}
closedir($dh);
return @rv;
}

# read_wg_conf(name)
# Parses a config file into a structure :
#  { name, file, iface => { opts => [[key,val]..], comments => [..] },
#    peers => [ { opts, comments, meta => {..}, disabled } ] }
sub read_wg_conf
{
my ($name) = @_;
my $file = &iface_file($name);
return &parse_wg_lines($name, $file, &read_file_lines($file, 1));
}

# parse_wg_lines(name, file, &lines)
sub parse_wg_lines
{
my ($name, $file, $lref) = @_;
my $conf = { 'name' => $name, 'file' => $file,
	     'iface' => { 'opts' => [], 'comments' => [], 'meta' => {} },
	     'peers' => [] };
my $cur;
foreach my $line (@$lref) {
	my $l = $line;
	my $dis = ($l =~ s/^\s*#DISABLED#\s?//) ? 1 : 0;
	$l =~ s/\r?\n?$//;
	if ($l =~ /^\s*\[(\w+)\]\s*$/) {
		if (lc($1) eq 'interface') {
			$cur = $conf->{'iface'};
			}
		elsif (lc($1) eq 'peer') {
			$cur = { 'opts' => [], 'comments' => [], 'meta' => {},
				 'disabled' => $dis };
			push(@{$conf->{'peers'}}, $cur);
			}
		else {
			$cur = undef;
			}
		}
	elsif (!$cur) {
		next;
		}
	elsif ($l =~ /^\s*#\s*(\w+)\s*=\s*(.*?)\s*$/ &&
	       grep { $_ eq $1 } @peer_meta_keys) {
		$cur->{'meta'}->{$1} = $2;
		}
	elsif ($l =~ /^\s*#/) {
		push(@{$cur->{'comments'}}, $l);
		}
	elsif ($l =~ /^\s*(\w+)\s*=\s*(.*?)\s*$/) {
		push(@{$cur->{'opts'}}, [ $1, $2 ]);
		}
	}
return $conf;
}

# write_wg_conf(&conf)
# Saves a config structure to disk with safe permissions
sub write_wg_conf
{
my ($conf) = @_;
my @out = ("[Interface]");
push(@out, @{$conf->{'iface'}->{'comments'}});
foreach my $o (@{$conf->{'iface'}->{'opts'}}) {
	push(@out, "$o->[0] = $o->[1]");
	}
foreach my $p (@{$conf->{'peers'}}) {
	my @pl = ("[Peer]");
	foreach my $k (@peer_meta_keys) {
		my $v = $p->{'meta'}->{$k};
		push(@pl, "# $k = $v") if (defined($v) && $v ne '');
		}
	push(@pl, @{$p->{'comments'}});
	foreach my $o (@{$p->{'opts'}}) {
		push(@pl, "$o->[0] = $o->[1]");
		}
	@pl = map { $disabled_prefix.$_ } @pl if ($p->{'disabled'});
	push(@out, "", @pl);
	}
my $file = $conf->{'file'};
&snapshot_conf($conf->{'name'});
&write_conf_text($file, join("\n", @out)."\n");
}

# write_conf_text(file, text)
# Writes a config file readable by root only
sub write_conf_text
{
my ($file, $data) = @_;
my $oldumask = umask(0077);
&open_lock_tempfile(WGCONF, ">$file");
&print_tempfile(WGCONF, $data);
&close_tempfile(WGCONF);
umask($oldumask);
&set_ownership_permissions(undef, undef, 0600, $file);
}

# opt_get(&section, key)
sub opt_get
{
my ($sec, $key) = @_;
foreach my $o (@{$sec->{'opts'}}) {
	return $o->[1] if (lc($o->[0]) eq lc($key));
	}
return undef;
}

# opt_get_all(&section, key)
sub opt_get_all
{
my ($sec, $key) = @_;
return map { $_->[1] } grep { lc($_->[0]) eq lc($key) } @{$sec->{'opts'}};
}

# opt_set(&section, key, value, ...)
# Replaces all values of an option. With no non-empty values, removes it.
sub opt_set
{
my ($sec, $key, @vals) = @_;
$sec->{'opts'} = [ grep { lc($_->[0]) ne lc($key) } @{$sec->{'opts'}} ];
foreach my $v (@vals) {
	$v = &clean_value($v);
	push(@{$sec->{'opts'}}, [ $key, $v ]) if ($v ne '');
	}
}

# iface_public_key(&conf)
sub iface_public_key
{
my ($conf) = @_;
my $priv = &opt_get($conf->{'iface'}, 'PrivateKey');
return $priv ? &wg_pubkey($priv) : undef;
}

# find_peer(&conf, pubkey)
sub find_peer
{
my ($conf, $pub) = @_;
foreach my $p (@{$conf->{'peers'}}) {
	return $p if (&opt_get($p, 'PublicKey') eq $pub);
	}
return undef;
}

############################ keys ############################

sub wg_genkey
{
my ($out, $err);
my $rc = &execute_command(&wg_cmd()." genkey", undef, \$out, \$err);
$out =~ s/\s+//g;
return $rc || !&valid_key($out) ? undef : $out;
}

sub wg_genpsk
{
my ($out, $err);
my $rc = &execute_command(&wg_cmd()." genpsk", undef, \$out, \$err);
$out =~ s/\s+//g;
return $rc || !&valid_key($out) ? undef : $out;
}

sub wg_pubkey
{
my ($priv) = @_;
return undef if (!&valid_key($priv));
my ($out, $err);
my $in = "$priv\n";
my $rc = &execute_command(&wg_cmd()." pubkey", \$in, \$out, \$err);
$out =~ s/\s+//g;
return $rc || !&valid_key($out) ? undef : $out;
}

############################ runtime status ############################

# get_wg_status()
# Returns { iface => { up, pubkey, port, peers => { pubkey => {..} } } }
sub get_wg_status
{
my ($out, $err);
&execute_command(&wg_cmd()." show all dump", undef, \$out, \$err);
my %st;
foreach my $l (split(/\n/, $out)) {
	my @f = split(/\t/, $l);
	if (@f == 5) {
		$st{$f[0]} ||= { 'peers' => { } };
		$st{$f[0]}->{'up'} = 1;
		$st{$f[0]}->{'pubkey'} = $f[2];
		$st{$f[0]}->{'port'} = $f[3];
		}
	elsif (@f >= 9) {
		$st{$f[0]} ||= { 'peers' => { }, 'up' => 1 };
		$st{$f[0]}->{'peers'}->{$f[1]} = {
			'endpoint' => $f[3] eq '(none)' ? '' : $f[3],
			'allowed' => $f[4] eq '(none)' ? '' : $f[4],
			'handshake' => int($f[5]),
			'rx' => $f[6],
			'tx' => $f[7],
			};
		}
	}
return \%st;
}

# peer_runtime_info(&status-peer)
# Returns (online, seconds since handshake or undef)
sub peer_runtime_info
{
my ($sp) = @_;
return (0, undef) if (!$sp || !$sp->{'handshake'});
my $ago = time() - $sp->{'handshake'};
$ago = 0 if ($ago < 0);
return ($ago <= $online_seconds ? 1 : 0, $ago);
}

sub nice_ago
{
my ($s) = @_;
return $text{'never'} if (!defined($s));
return &text('ago_s', $s) if ($s < 60);
return &text('ago_m', int($s/60)) if ($s < 3600);
return &text('ago_h', int($s/3600)) if ($s < 86400);
return &text('ago_d', int($s/86400));
}

############################ interface control ############################

# run_cmd(command)
# Returns an error message on failure, undef on success
sub run_cmd
{
my ($cmd) = @_;
my $out;
my $rc = &execute_command($cmd, undef, \$out, \$out);
return $rc ? ($out || $cmd) : undef;
}

# iface_action(name, up|down|restart|reload)
sub iface_action
{
my ($name, $act) = @_;
my $q = quotemeta(&iface_file($name));
my $quick = &wg_quick_cmd();
if ($act eq 'up') {
	return &run_cmd("$quick up $q");
	}
elsif ($act eq 'down') {
	return &run_cmd("$quick down $q");
	}
elsif ($act eq 'restart') {
	&run_cmd("$quick down $q");
	return &run_cmd("$quick up $q");
	}
elsif ($act eq 'reload') {
	return &iface_reload($name);
	}
return "Unknown action";
}

# iface_reload(name)
# Applies config changes to a running interface without dropping peers
sub iface_reload
{
my ($name) = @_;
my ($stripped, $err);
my $q = quotemeta(&iface_file($name));
my $rc = &execute_command(&wg_quick_cmd()." strip $q", undef, \$stripped, \$err);
return $err || "wg-quick strip failed" if ($rc);
my $tmp = &transname();
my $oldumask = umask(0077);
open(my $fh, ">", $tmp) || return "Failed to write $tmp : $!";
print $fh $stripped;
close($fh);
umask($oldumask);
my $res = &run_cmd(&wg_cmd()." syncconf ".quotemeta($name)." ".quotemeta($tmp));
&unlink_file($tmp);
return $res;
}

# apply_if_running(name)
# Reloads the interface if it is up. Returns an error message or undef.
sub apply_if_running
{
my ($name) = @_;
my $st = &get_wg_status();
return undef if (!$st->{$name});
return &iface_reload($name);
}

sub boot_supported
{
return &has_command("systemctl") ? 1 : 0;
}

sub iface_boot_enabled
{
my ($name) = @_;
return 0 if (!&boot_supported());
my $out;
my $rc = &execute_command("systemctl is-enabled ".quotemeta("wg-quick\@$name"),
			  undef, \$out, \$out);
return $rc ? 0 : 1;
}

sub iface_set_boot
{
my ($name, $enable) = @_;
return &run_cmd("systemctl ".($enable ? "enable" : "disable")." ".
		quotemeta("wg-quick\@$name"));
}

############################ addressing ############################

sub ip2int
{
my @o = split(/\./, $_[0]);
return ($o[0] << 24) | ($o[1] << 16) | ($o[2] << 8) | $o[3];
}

sub int2ip
{
my ($n) = @_;
return join(".", ($n >> 24) & 255, ($n >> 16) & 255, ($n >> 8) & 255, $n & 255);
}

# iface_subnets(&conf)
# Returns the network CIDR of each interface address, like 10.0.0.0/24
sub iface_subnets
{
my ($conf) = @_;
my @rv;
foreach my $a (map { split(/\s*,\s*/, $_) } &opt_get_all($conf->{'iface'}, 'Address')) {
	my ($ip, $len) = split(/\//, $a);
	if ($ip =~ /^\d+\.\d+\.\d+\.\d+$/) {
		my $mask = $len == 0 ? 0 : (0xFFFFFFFF << (32 - $len)) & 0xFFFFFFFF;
		push(@rv, &int2ip(&ip2int($ip) & $mask)."/$len");
		}
	elsif ($ip =~ /:/) {
		my @g = &expand_ipv6($ip);
		for(my $i = 0; $i < 8; $i++) {
			my $bits = $len - 16 * $i;
			$bits = 0 if ($bits < 0);
			$bits = 16 if ($bits > 16);
			$g[$i] &= (0xFFFF << (16 - $bits)) & 0xFFFF;
			}
		push(@rv, &compress_ipv6(@g)."/$len");
		}
	}
return @rv;
}

sub expand_ipv6
{
my ($a) = @_;
my ($head, $tail) = split(/::/, $a, 2);
my @h = map { hex($_) } split(/:/, $head);
return @h if (index($a, '::') < 0);
my @t = map { hex($_) } split(/:/, $tail);
return (@h, (0) x (8 - @h - @t), @t);
}

sub compress_ipv6
{
my @g = @_;
my ($best, $blen, $cur, $clen) = (-1, 1, -1, 0);
for(my $i = 0; $i < 8; $i++) {
	if ($g[$i] == 0) {
		($cur, $clen) = ($i, 0) if ($cur < 0 || $g[$i-1] != 0);
		$clen++;
		($best, $blen) = ($cur, $clen) if ($clen > $blen);
		}
	}
my @h = map { sprintf("%x", $_) } @g;
return join(":", @h) if ($best < 0);
return join(":", @h[0..$best-1])."::".join(":", @h[$best+$blen..7]);
}

# next_free_ip(&conf)
# Returns the next unused IPv4 /32 in the interface subnet, or undef
sub next_free_ip
{
my ($conf) = @_;
my @addrs = map { split(/\s*,\s*/, $_) } &opt_get_all($conf->{'iface'}, 'Address');
my ($a4) = grep { /^\d+\.\d+\.\d+\.\d+\/\d+$/ } @addrs;
return undef if (!$a4);
my ($ip, $len) = split(/\//, $a4);
my $mask = $len == 0 ? 0 : (0xFFFFFFFF << (32 - $len)) & 0xFFFFFFFF;
my $net = &ip2int($ip) & $mask;
my $bcast = $net | (~$mask & 0xFFFFFFFF);
my %used = ( &ip2int($ip) => 1 );
foreach my $p (@{$conf->{'peers'}}) {
	foreach my $a (split(/\s*,\s*/, &opt_get($p, 'AllowedIPs'))) {
		$used{&ip2int($1)} = 1 if ($a =~ /^(\d+\.\d+\.\d+\.\d+)\//);
		}
	}
for(my $i = $net + 1; $i < $bcast; $i++) {
	return &int2ip($i)."/32" if (!$used{$i});
	}
return undef;
}

############################ client config ############################

# build_client_config(&conf, &peer)
# Returns (text, error)
sub build_client_config
{
my ($conf, $peer) = @_;
my $m = $peer->{'meta'};
return (undef, $text{'err_nopriv'}) if (!$m->{'PrivateKey'});
my $spub = &iface_public_key($conf);
return (undef, $text{'err_nopub'}) if (!$spub);
my $port = &opt_get($conf->{'iface'}, 'ListenPort');
my $ep = $m->{'ClientEndpoint'} || $config{'default_endpoint'} ||
	 &get_system_hostname();
$ep .= ":$port" if ($ep !~ /:\d+$/ && $port);
my $dns = $m->{'ClientDNS'};
$dns = $config{'default_dns'} if (!defined($dns) || $dns eq '');
my $allowed = join(", ", &peer_client_allowed($conf, $peer));
my $ka = $m->{'ClientKeepalive'};
$ka = $config{'default_keepalive'} if (!defined($ka) || $ka eq '');
my $mtu = $m->{'ClientMTU'};
$mtu = $config{'default_mtu'} if (!defined($mtu) || $mtu eq '');
my @l = ("[Interface]", "PrivateKey = $m->{'PrivateKey'}",
	 "Address = ".&opt_get($peer, 'AllowedIPs'));
push(@l, "DNS = $dns") if ($dns);
push(@l, "MTU = $mtu") if ($mtu);
push(@l, "", "[Peer]", "PublicKey = $spub");
my $psk = &opt_get($peer, 'PresharedKey');
push(@l, "PresharedKey = $psk") if ($psk);
push(@l, "AllowedIPs = $allowed", "Endpoint = $ep");
push(@l, "PersistentKeepalive = $ka") if ($ka);
return (join("\n", @l)."\n", undef);
}

# peer_filename(&peer)
sub peer_filename
{
my ($peer) = @_;
my $n = $peer->{'meta'}->{'Name'} || substr(&opt_get($peer, 'PublicKey'), 0, 8);
$n =~ s/[^A-Za-z0-9._-]/_/g;
return "$n.conf";
}

############################ statistics ############################

sub stats_dir
{
return "$module_var_directory/stats";
}

sub stats_file
{
return &stats_dir()."/".$_[0].".log";
}

# ensure_collector_job()
# Creates, updates or removes the scheduled statistics collector
sub ensure_collector_job
{
&foreign_require("webmincron");
my ($job) = grep { $_->{'module'} eq $module_name &&
		   $_->{'func'} eq 'collect_stats' }
		 &webmincron::list_webmin_crons();
my $interval = int($config{'collect_interval'} || 60);
$interval = 10 if ($interval < 10);
if ($config{'collect_stats'}) {
	if (!$job) {
		&webmincron::create_webmin_cron({ 'user' => 'root',
			'module' => $module_name, 'func' => 'collect_stats',
			'interval' => $interval });
		}
	elsif ($job->{'interval'} != $interval) {
		$job->{'interval'} = $interval;
		&webmincron::modify_webmin_cron($job);
		}
	}
elsif ($job) {
	&webmincron::delete_webmin_cron($job);
	}
}

# collect_stats()
# Called periodically by webmincron : appends raw peer counters to the logs
sub collect_stats
{
return if (!$config{'collect_stats'});
&make_dir(&stats_dir(), 0700, 1) if (!-d &stats_dir());
my $st = &get_wg_status();
my $now = time();
foreach my $if (keys %$st) {
	next if (!&valid_iface_name($if));
	open(my $fh, ">>", &stats_file($if)) || next;
	foreach my $pub (keys %{$st->{$if}->{'peers'}}) {
		my $p = $st->{$if}->{'peers'}->{$pub};
		print $fh join(" ", $now, $pub, $p->{'rx'}, $p->{'tx'},
				    $p->{'handshake'}), "\n";
		}
	close($fh);
	}
&prune_stats($now);
}

# prune_stats(now)
# Removes samples older than the retention period, at most once per hour
sub prune_stats
{
my ($now) = @_;
my $stamp = &stats_dir()."/.pruned";
my @s = stat($stamp);
return if (@s && $now - $s[9] < 3600);
my $days = int($config{'retention_days'} || 30);
my $min = $now - $days * 86400;
foreach my $f (glob(&stats_dir()."/*.log")) {
	open(my $in, "<", $f) || next;
	my @keep = grep { /^(\d+) / && $1 >= $min } <$in>;
	close($in);
	open(my $out, ">", "$f.tmp") || next;
	print $out @keep;
	close($out);
	rename("$f.tmp", $f);
	}
open(my $st, ">", $stamp);
close($st) if ($st);
utime($now, $now, $stamp);
}

# get_stats_series(iface, [pubkey], seconds, buckets)
# Returns { start, step, rx => [..], tx => [..] } with traffic per bucket
sub get_stats_series
{
my ($iface, $pub, $secs, $n) = @_;
my $now = time();
my $start = $now - $secs;
my $step = $secs / $n;
my (@rx, @tx);
for(my $i = 0; $i < $n; $i++) { $rx[$i] = 0; $tx[$i] = 0; }
if (open(my $fh, "<", &stats_file($iface))) {
	my %prev;
	while(my $l = <$fh>) {
		my ($t, $k, $r, $x) = split(/\s+/, $l);
		next if ($pub && $k ne $pub);
		next if (!defined($x));
		# Only counters seen inside the window give a delta
		my $p = $prev{$k};
		$prev{$k} = [ $r, $x ];
		next if ($t < $start || !$p);
		my $dr = $r >= $p->[0] ? $r - $p->[0] : $r;
		my $dx = $x >= $p->[1] ? $x - $p->[1] : $x;
		my $b = int(($t - $start) / $step);
		$b = $n - 1 if ($b >= $n);
		$rx[$b] += $dr;
		$tx[$b] += $dx;
		}
	close($fh);
	}
return { 'start' => $start, 'step' => $step, 'rx' => \@rx, 'tx' => \@tx };
}

############################ output helpers ############################

sub json_str
{
my ($s) = @_;
$s =~ s/([\\"])/\\$1/g;
$s =~ s/\n/\\n/g;
$s =~ s/\r/\\r/g;
$s =~ s/\t/\\t/g;
$s =~ s/([\x00-\x1f])/sprintf("\\u%04x", ord($1))/ge;
$s =~ s/</\\u003c/g;
return "\"$s\"";
}

sub to_json
{
my ($d) = @_;
return "null" if (!defined($d));
if (ref($d) eq 'ARRAY') {
	return "[".join(",", map { &to_json($_) } @$d)."]";
	}
if (ref($d) eq 'HASH') {
	return "{".join(",", map { &json_str($_).":".&to_json($d->{$_}) }
				 sort keys %$d)."}";
	}
return $d if ($d =~ /^-?\d+(\.\d+)?$/);
return &json_str($d);
}

############################ network map ############################

# cidr_range(cidr)
# Returns (family, start, end) with Math::BigInt bounds, or () if invalid
sub cidr_range
{
my ($c) = @_;
my ($ip, $len) = split(/\//, $c);
my ($fam, $bits, $val);
if ($ip =~ /^\d+\.\d+\.\d+\.\d+$/) {
	($fam, $bits) = (4, 32);
	$val = Math::BigInt->new(&ip2int($ip));
	}
elsif ($ip =~ /^[0-9a-fA-F:]+$/ && $ip =~ /:/) {
	($fam, $bits) = (6, 128);
	$val = Math::BigInt->new(0);
	foreach my $g (&expand_ipv6($ip)) {
		$val->bmul(65536);
		$val->badd($g);
		}
	}
else {
	return ();
	}
$len = $bits if (!defined($len) || $len eq '');
return () if ($len !~ /^\d+$/ || $len > $bits);
my $size = Math::BigInt->new(1)->blsft($bits - $len);
my $start = $val->copy();
$start->bdiv($size);
$start->bmul($size);
my $end = $start->copy()->badd($size)->bsub(1);
return ($fam, $start, $end);
}

sub ranges_overlap
{
my ($a, $b) = @_;
return 0 if (!@$a || !@$b || $a->[0] != $b->[0]);
return ($a->[1]->bcmp($b->[2]) <= 0 && $b->[1]->bcmp($a->[2]) <= 0) ? 1 : 0;
}

sub cidrs_overlap
{
my @a = &cidr_range($_[0]);
my @b = &cidr_range($_[1]);
return &ranges_overlap(\@a, \@b);
}

# cidr_covers(big, small)
# Returns 1 if the small network is entirely inside the big one
sub cidr_covers
{
my @a = &cidr_range($_[0]);
my @b = &cidr_range($_[1]);
return 0 if (!@a || !@b || $a[0] != $b[0]);
return ($a[1]->bcmp($b[1]) <= 0 && $a[2]->bcmp($b[2]) >= 0) ? 1 : 0;
}

sub any_covers
{
my ($list, $cidr) = @_;
foreach my $c (@$list) {
	return 1 if (&cidr_covers($c, $cidr));
	}
return 0;
}

# peer_client_allowed(&conf, &peer)
# Returns the networks the client sends through the tunnel
sub peer_client_allowed
{
my ($conf, $peer) = @_;
my $ca = $peer->{'meta'}->{'ClientAllowedIPs'};
my @l = $ca ? split(/\s*,\s*/, $ca) : &iface_subnets($conf);
return @l ? @l : ('0.0.0.0/0', '::/0');
}

# client_mode(&client-allowed, &subnets)
# Returns full, split or custom
sub client_mode
{
my ($ca, $subs) = @_;
return 'full' if (grep { m{^(0\.0\.0\.0|::)/0$} } @$ca);
return 'split' if (join(',', sort @$ca) eq join(',', sort @$subs));
return 'custom';
}

# peer_split_allowed(&conf, &peer)
# Returns (&own-addresses, &networks-behind-peer) from the server-side AllowedIPs
sub peer_split_allowed
{
my ($conf, $peer) = @_;
my @subs = &iface_subnets($conf);
my (@own, @nets);
foreach my $a (split(/\s*,\s*/, &opt_get($peer, 'AllowedIPs'))) {
	next if ($a eq '');
	my ($ip, $len) = split(/\//, $a);
	my $host = ($ip !~ /:/ && $len == 32) || ($ip =~ /:/ && $len == 128);
	if ($host && &any_covers(\@subs, $a)) {
		push(@own, $a);
		}
	else {
		push(@nets, $a);
		}
	}
return (\@own, \@nets);
}

# get_system_routes()
# Returns [ network, device ] for each route on the host
sub get_system_routes
{
my @rv;
foreach my $fam ('-4', '-6') {
	my ($out, $err);
	&execute_command("ip $fam -o route show", undef, \$out, \$err);
	foreach my $l (split(/\n/, $out)) {
		my ($dest) = split(/\s+/, $l);
		next if ($dest !~ /^[0-9a-fA-F:.]+(\/\d+)?$/);
		my ($dev) = $l =~ /\bdev\s+(\S+)/;
		push(@rv, [ $dest, $dev ]);
		}
	}
return @rv;
}

# detect_conflicts(&confs)
# Returns a list of { text, marks } warnings about overlapping networks
sub detect_conflicts
{
my ($confs) = @_;
my (@warn, %seen, %rc);
my %wgdev = map { $_->{'name'}, 1 } @$confs;
my $range = sub { $rc{$_[0]} ||= [ &cidr_range($_[0]) ] };
my $warn = sub {
	my ($key, $marks, @args) = @_;
	my $t = &text($key, map { &html_escape($_) } @args);
	push(@warn, { 'text' => $t, 'marks' => $marks }) if (!$seen{$t}++);
	};

my @items;
my @subnets;
foreach my $conf (@$confs) {
	my $if = $conf->{'name'};
	push(@subnets, map { [ $if, $_ ] } &iface_subnets($conf));
	foreach my $p (@{$conf->{'peers'}}) {
		next if ($p->{'disabled'});
		my $pub = &opt_get($p, 'PublicKey');
		my ($own, $nets) = &peer_split_allowed($conf, $p);
		my $who = "$if / ".($p->{'meta'}->{'Name'} || substr($pub, 0, 8));
		foreach my $c (@$own) {
			push(@items, { 'if' => $if, 'pub' => $pub, 'who' => $who,
				       'cidr' => $c, 'own' => 1, 'key' => "$if|$pub|$c" });
			}
		foreach my $c (@$nets) {
			push(@items, { 'if' => $if, 'pub' => $pub, 'who' => $who,
				       'cidr' => $c, 'own' => 0, 'key' => "$if|$pub|$c" });
			}
		}
	}

# Peers claiming overlapping addresses
for(my $i = 0; $i < @items; $i++) {
	my $a = $items[$i];
	next if ($a->{'cidr'} =~ m{/0$});
	for(my $j = $i + 1; $j < @items; $j++) {
		my $b = $items[$j];
		next if ($b->{'cidr'} =~ m{/0$});
		next if ($a->{'pub'} eq $b->{'pub'} && $a->{'if'} eq $b->{'if'});
		next if ($a->{'if'} ne $b->{'if'} && ($a->{'own'} || $b->{'own'}));
		if (&ranges_overlap($range->($a->{'cidr'}), $range->($b->{'cidr'}))) {
			&$warn('map_w_peers', { $a->{'key'} => 1, $b->{'key'} => 1 },
			       $a->{'who'}, $a->{'cidr'}, $b->{'who'}, $b->{'cidr'});
			}
		}
	}

# Interfaces with overlapping subnets
for(my $i = 0; $i < @subnets; $i++) {
	for(my $j = $i + 1; $j < @subnets; $j++) {
		next if ($subnets[$i]->[0] eq $subnets[$j]->[0]);
		if (&ranges_overlap($range->($subnets[$i]->[1]), $range->($subnets[$j]->[1]))) {
			&$warn('map_w_ifaces', { }, $subnets[$i]->[0], $subnets[$i]->[1],
			       $subnets[$j]->[0], $subnets[$j]->[1]);
			}
		}
	}

my @routes = grep { !$wgdev{$_->[1]} && $_->[0] !~ m{/0$} && $_->[0] ne 'default' }
		  &get_system_routes();
foreach my $it (grep { !$_->{'own'} } @items) {
	my $c = $it->{'cidr'};
	if ($c =~ m{^(0\.0\.0\.0|::)/0$}) {
		&$warn('map_w_default', { $it->{'key'} => 1 }, $it->{'who'});
		next;
		}
	foreach my $s (@subnets) {
		if (&ranges_overlap($range->($c), $range->($s->[1]))) {
			&$warn('map_w_subnet', { $it->{'key'} => 1 }, $it->{'who'}, $c,
			       $s->[0], $s->[1]);
			}
		}
	foreach my $r (@routes) {
		if (&ranges_overlap($range->($c), $range->($r->[0]))) {
			&$warn('map_w_route', { $it->{'key'} => 1 }, $it->{'who'}, $c,
			       $r->[0], $r->[1] || '-');
			}
		}
	}
return @warn;
}

# build_network_map()
# Returns { ifaces => [ { name, up, address, peers => [..] } ], warnings => [..] }
sub build_network_map
{
my $st = &get_wg_status();
my @confs = map { &read_wg_conf($_) } &list_interfaces();
my $map = { 'ifaces' => [], 'warnings' => [ &detect_conflicts(\@confs) ] };
foreach my $conf (@confs) {
	my $is = $st->{$conf->{'name'}};
	my @subs = &iface_subnets($conf);
	my @plist;
	foreach my $p (@{$conf->{'peers'}}) {
		my $pub = &opt_get($p, 'PublicKey');
		my ($own, $nets) = &peer_split_allowed($conf, $p);
		my ($online) = &peer_runtime_info($is ? $is->{'peers'}->{$pub} : undef);
		my @ca = &peer_client_allowed($conf, $p);
		push(@plist, { 'name' => $p->{'meta'}->{'Name'} || substr($pub, 0, 8),
			       'pub' => $pub, 'disabled' => $p->{'disabled'} ? 1 : 0,
			       'online' => $online, 'own' => $own, 'nets' => $nets,
			       'client_allowed' => \@ca,
			       'mode' => &client_mode(\@ca, \@subs) });
		}
	# Networks behind other peers that this peer's client config does not route
	foreach my $pe (@plist) {
		my (@reach, @missing);
		foreach my $q (@plist) {
			next if ($q eq $pe || $q->{'disabled'} || $pe->{'disabled'});
			foreach my $n (@{$q->{'nets'}}) {
				if (&any_covers($pe->{'client_allowed'}, $n)) {
					push(@reach, $n);
					}
				else {
					push(@missing, $n);
					}
				}
			}
		$pe->{'reach'} = \@reach;
		$pe->{'missing'} = \@missing;
		}
	push(@{$map->{'ifaces'}}, { 'name' => $conf->{'name'}, 'up' => $is ? 1 : 0,
		'address' => join(', ', &opt_get_all($conf->{'iface'}, 'Address')),
		'peers' => \@plist });
	}
return $map;
}

# render_map_svg(&map, [only-iface])
# Draws interface -> peer -> network columns as inline SVG
sub render_map_svg
{
my ($map, $only) = @_;
my %mark;
foreach my $w (@{$map->{'warnings'}}) {
	$mark{$_} = 1 foreach (keys %{$w->{'marks'}});
	}
my $esc = sub { &html_escape(length($_[0]) > 34 ? substr($_[0], 0, 33)."..." : $_[0]) };
my $modelabel = { 'full' => $text{'map_full'}, 'split' => $text{'map_split'},
		  'custom' => $text{'map_custom'} };
my (@edges, @boxes);
my $y = 10;
foreach my $if (@{$map->{'ifaces'}}) {
	next if ($only && $if->{'name'} ne $only);
	my $top = $y;
	my @pcy;
	foreach my $p (@{$if->{'peers'}}) {
		my $n = scalar(@{$p->{'nets'}});
		my $h = $n * 34 > 52 ? $n * 34 : 52;
		my $cy = $y + $h / 2;
		push(@pcy, $cy);
		my $col = $p->{'disabled'} ? '#bbb' : $p->{'online'} ? '#2a9d3f' : '#888';
		my $dash = $p->{'disabled'} ? " stroke-dasharray='5,3'" : "";
		my $bad = grep { $mark{"$if->{'name'}|$p->{'pub'}|$_"} } @{$p->{'own'}};
		$col = '#d33' if ($bad);
		push(@boxes, "<rect x='330' y='".($cy - 23)."' width='230' height='46' rx='6' ".
			     "fill='#fff' stroke='$col' stroke-width='2'$dash />");
		push(@boxes, "<text x='340' y='".($cy - 3)."' font-weight='bold'>".
			     $esc->($p->{'name'})."</text>");
		push(@boxes, "<text x='340' y='".($cy + 13)."' font-size='11' fill='#555'>".
			     $esc->(join(', ', @{$p->{'own'}})." - ".$modelabel->{$p->{'mode'}}).
			     "</text>");
		my $ny = $y + ($h - $n * 34) / 2;
		foreach my $net (@{$p->{'nets'}}) {
			my $ncy = $ny + 17;
			my $nc = $mark{"$if->{'name'}|$p->{'pub'}|$net"} ? '#d33' : '#e1802a';
			push(@edges, "<line x1='560' y1='$cy' x2='690' y2='$ncy' stroke='#aaa' />");
			push(@boxes, "<rect x='690' y='".($ncy - 14)."' width='200' height='28' ".
				     "rx='14' fill='#fff7e6' stroke='$nc' stroke-width='2' />");
			push(@boxes, "<text x='790' y='".($ncy + 4)."' text-anchor='middle'>".
				     $esc->($net)."</text>");
			$ny += 34;
			}
		$y += $h + 10;
		}
	my $block = $y - $top - 10;
	if ($block < 64) {
		$block = 64;
		$y = $top + 74;
		}
	my $icy = $top + $block / 2;
	my $col = $if->{'up'} ? '#2a7de1' : '#888';
	push(@boxes, "<rect x='10' y='".($icy - 32)."' width='210' height='64' rx='8' ".
		     "fill='#e8f0fe' stroke='$col' stroke-width='2' />");
	push(@boxes, "<text x='20' y='".($icy - 10)."' font-weight='bold'>".
		     $esc->($if->{'name'})."</text>");
	push(@boxes, "<text x='20' y='".($icy + 6)."' font-size='11' fill='#555'>".
		     $esc->($if->{'address'})."</text>");
	push(@boxes, "<text x='20' y='".($icy + 22)."' font-size='11' fill='$col'>".
		     ($if->{'up'} ? $text{'iface_up'} : $text{'iface_down'})."</text>");
	my $i = 0;
	foreach my $p (@{$if->{'peers'}}) {
		my $pcy = $pcy[$i++];
		push(@edges, "<path d='M220,$icy C275,$icy 275,$pcy 330,$pcy' ".
			     "fill='none' stroke='#aaa' />");
		}
	$y += 16;
	}
return "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 900 ".($y + 4)."' ".
       "width='100%' style='max-width:900px;background:#fff;border:1px solid #ccc' ".
       "font-family='sans-serif' font-size='12' fill='#222'>".
       join("\n", @edges, @boxes)."</svg>";
}

############################ backup and restore ############################

sub backup_dir
{
return "$module_var_directory/backups";
}

sub backup_keep
{
my $k = $config{'backup_keep'};
return (defined($k) && $k =~ /^\d+$/) ? $k : 20;
}

# list_snapshots(name)
# Returns { ts, file, size } for each saved copy of an interface, newest first
sub list_snapshots
{
my ($name) = @_;
my $dir = &backup_dir()."/$name";
my @rv;
opendir(my $dh, $dir) || return ();
foreach my $f (readdir($dh)) {
	if ($f =~ /^(\d{9,11})\.conf$/) {
		push(@rv, { 'ts' => $1, 'file' => "$dir/$f", 'size' => (-s "$dir/$f") });
		}
	}
closedir($dh);
return sort { $b->{'ts'} <=> $a->{'ts'} } @rv;
}

# list_snapshot_ifaces()
# Returns names of interfaces that have saved copies, including deleted ones
sub list_snapshot_ifaces
{
my @rv;
opendir(my $dh, &backup_dir()) || return ();
foreach my $f (sort readdir($dh)) {
	my @snaps = &valid_iface_name($f) ? &list_snapshots($f) : ();
	push(@rv, $f) if (@snaps);
	}
closedir($dh);
return @rv;
}

# snapshot_conf(name)
# Saves a copy of the current config file before it is changed or removed
sub snapshot_conf
{
my ($name) = @_;
my $keep = &backup_keep();
my $file = &iface_file($name);
return if ($keep < 1 || !&valid_iface_name($name) || !-r $file);
my $dir = &backup_dir()."/$name";
if (!-d $dir) {
	&make_dir($dir, 0700, 1);
	chmod(0700, &backup_dir(), $dir);
	}
my $data = &read_file_contents($file);
my ($last) = &list_snapshots($name);
return if ($last && &read_file_contents($last->{'file'}) eq $data);
my $oldumask = umask(0077);
if (open(my $fh, ">", "$dir/".time().".conf")) {
	print $fh $data;
	close($fh);
	}
umask($oldumask);
my @all = &list_snapshots($name);
foreach my $s (@all[$keep .. $#all]) {
	&unlink_file($s->{'file'});
	}
}

# restore_snapshot(name, ts)
# Returns an error message or undef
sub restore_snapshot
{
my ($name, $ts) = @_;
&valid_iface_name($name) && $ts =~ /^\d{9,11}$/ || return $text{'err_nosnap'};
my $src = &backup_dir()."/$name/$ts.conf";
-r $src || return $text{'err_nosnap'};
my $data = &read_file_contents($src);
&snapshot_conf($name);
&write_conf_text(&iface_file($name), $data);
return undef;
}

# make_backup_archive()
# Returns (path of a temporary .tar.gz with all interface configs, error)
sub make_backup_archive
{
my @names = &list_interfaces();
return (undef, $text{'err_nobackup'}) if (!@names);
&has_command('tar') || return (undef, &text('err_nocmd', 'tar'));
my $tmp = &transname();
my $oldumask = umask(0077);
my $err = &run_cmd("tar czf ".quotemeta($tmp)." -C ".quotemeta(&config_dir())." ".
		   join(" ", map { quotemeta("$_.conf") } @names));
umask($oldumask);
return $err ? (undef, $err) : ($tmp, undef);
}

# restore_archive(data)
# Validates and restores configs from an uploaded .tar.gz.
# Returns (&restored-names, error)
sub restore_archive
{
my ($data) = @_;
return (undef, $text{'err_empty'}) if (!length($data));
return (undef, $text{'err_toobig'}) if (length($data) > 10 * 1024 * 1024);
&has_command('tar') || return (undef, &text('err_nocmd', 'tar'));
my $tmp = &transname();
my $dir = &transname();
my $oldumask = umask(0077);
my $fail = sub {
	umask($oldumask);
	&unlink_file($tmp);
	&unlink_file($dir);
	return (undef, $_[0]);
	};
mkdir($dir, 0700);
open(my $fh, ">", $tmp) || return &$fail($!);
binmode($fh);
print $fh $data;
close($fh);
umask($oldumask);

# Only plain files named <interface>.conf are accepted
my ($names, $types, $err);
my $q = quotemeta($tmp);
&execute_command("tar tzf $q", undef, \$names, \$err) &&
	return &$fail($text{'err_badarchive'});
&execute_command("tar tzvf $q", undef, \$types, \$err) &&
	return &$fail($text{'err_badarchive'});
my @n = split(/\n/, $names);
my @t = split(/\n/, $types);
return &$fail($text{'err_badarchive'}) if (!@n || @n != @t || @n > 50);
my @found;
for(my $i = 0; $i < @n; $i++) {
	next if ($n[$i] =~ m{^\./?$} && $t[$i] =~ /^d/);
	my ($base) = $n[$i] =~ /^(?:\.\/)?([^\/]+)\.conf$/;
	return &$fail($text{'err_badarchive'})
		if (!defined($base) || !&valid_iface_name($base) || $t[$i] !~ /^-/);
	push(@found, $base);
	}
return &$fail($text{'err_badarchive'}) if (!@found);
&execute_command("tar xzf $q -C ".quotemeta($dir).
		" --no-same-owner --no-same-permissions", undef, \$names, \$err) &&
	return &$fail($text{'err_badarchive'});
my %content;
foreach my $n (@found) {
	my $c = &read_file_contents("$dir/$n.conf");
	return &$fail(&text('err_badconf', &html_escape($n)))
		if ($c !~ /^\s*\[Interface\]/mi || $c !~ /^\s*PrivateKey\s*=/mi);
	$content{$n} = $c;
	}
foreach my $n (@found) {
	&snapshot_conf($n);
	&write_conf_text(&iface_file($n), $content{$n});
	}
&unlink_file($tmp);
&unlink_file($dir);
return ([ @found ], undef);
}

# parse_import(name, text, [address-optional])
# Validates a pasted or uploaded wg-quick config. Returns (&conf, error)
sub parse_import
{
my ($name, $data, $loose) = @_;
$data =~ s/\r//g;
return (undef, $text{'err_empty'}) if ($data !~ /\S/);
return (undef, $text{'err_toobig'}) if (length($data) > 65536 || $data =~ /\x00/);
my $conf = &parse_wg_lines($name, &iface_file($name), [ split(/\n/, $data) ]);
my $sec = $conf->{'iface'};
&valid_key(&opt_get($sec, 'PrivateKey')) || return (undef, $text{'err_import_key'});
my @addr = map { split(/\s*,\s*/, $_) } &opt_get_all($sec, 'Address');
return (undef, $text{'err_address'}) if ((!@addr && !$loose) || grep { !&valid_cidr($_) } @addr);
my $port = &opt_get($sec, 'ListenPort');
return (undef, $text{'err_port'})
	if (defined($port) && ($port !~ /^\d+$/ || $port < 1 || $port > 65535));
foreach my $p (@{$conf->{'peers'}}) {
	&valid_key(&opt_get($p, 'PublicKey')) || return (undef, $text{'err_pubkey'});
	my $psk = &opt_get($p, 'PresharedKey');
	return (undef, $text{'err_pubkey'}) if (defined($psk) && !&valid_key($psk));
	my $al = &opt_get($p, 'AllowedIPs');
	return (undef, $text{'err_allowed'}) if (defined($al) && !&valid_cidr_list($al));
	my $ep = &opt_get($p, 'Endpoint');
	return (undef, $text{'err_endpoint'}) if (defined($ep) && !&valid_endpoint($ep));
	}
return ($conf, undef);
}

# load_script_then(src, js)
# Loads a script and runs js once it is ready, as themes may inject page scripts asynchronously
sub load_script_then
{
my ($src, $js) = @_;
return "<script>(function() {\n".
       "var s = document.createElement('script');\n".
       "s.src = ".&json_str($src).";\n".
       "s.onload = function() {\n$js};\n".
       "document.head.appendChild(s);\n".
       "})();</script>\n";
}

# load_iface_or_error(name)
# Validates a name from user input and returns the parsed config
sub load_iface_or_error
{
my ($name) = @_;
&valid_iface_name($name) || &error($text{'err_name'});
-r &iface_file($name) || &error(&text('err_noiface', &html_escape($name)));
return &read_wg_conf($name);
}

1;
