do 'wireguard-lib.pl';

# module_uninstall()
# Removes the scheduled statistics collector when the module is deleted
sub module_uninstall
{
&foreign_require("webmincron");
foreach my $job (&webmincron::list_webmin_crons()) {
	if ($job->{'module'} eq $module_name && $job->{'func'} eq 'collect_stats') {
		&webmincron::delete_webmin_cron($job);
		}
	}
}

1;
