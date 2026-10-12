#!/usr/bin/perl
# Save default settings

require './wireguard-lib.pl';
&error_setup($text{'save_err'});
&ReadParse();

if ($in{'endpoint_def'}) {
	$config{'default_endpoint'} = '';
	}
else {
	&valid_endpoint($in{'endpoint'}) || &error($text{'err_endpoint'});
	$config{'default_endpoint'} = $in{'endpoint'};
	}

$in{'dns'} =~ s/^\s+|\s+$//g;
$in{'dns'} eq '' || &valid_dns_list($in{'dns'}) || &error($text{'err_dns'});
$config{'default_dns'} = $in{'dns'};

if ($in{'keepalive_def'}) {
	$config{'default_keepalive'} = '';
	}
else {
	$in{'keepalive'} =~ /^\d+$/ && $in{'keepalive'} <= 65535 ||
		&error($text{'err_keepalive'});
	$config{'default_keepalive'} = $in{'keepalive'};
	}

if ($in{'mtu_def'}) {
	$config{'default_mtu'} = '';
	}
else {
	$in{'mtu'} =~ /^\d+$/ && $in{'mtu'} >= 576 && $in{'mtu'} <= 9000 ||
		&error($text{'err_mtu'});
	$config{'default_mtu'} = $in{'mtu'};
	}

$in{'interval'} =~ /^\d+$/ && $in{'interval'} >= 10 || &error($text{'err_interval'});
$in{'retention'} =~ /^\d+$/ && $in{'retention'} >= 1 || &error($text{'err_retention'});
$config{'collect_stats'} = $in{'collect'} ? 1 : 0;
$config{'collect_interval'} = $in{'interval'};
$config{'retention_days'} = $in{'retention'};

$in{'keep'} =~ /^\d+$/ && $in{'keep'} <= 1000 || &error($text{'err_keep'});
$config{'backup_keep'} = $in{'keep'};

&lock_file("$module_config_directory/config");
&save_module_config();
&unlock_file("$module_config_directory/config");
&ensure_collector_job();
&webmin_log('modify', 'defaults');
&redirect("");
