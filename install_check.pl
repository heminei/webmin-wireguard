do 'wireguard-lib.pl';

# is_installed(mode)
# Returns 1 if WireGuard tools are present, 2 if the module is also configured
sub is_installed
{
my ($mode) = @_;
return 0 if (&check_wireguard());
return $mode ? (-d $config{'config_dir'} ? 2 : 1) : 1;
}

1;
