do 'wireguard-lib.pl';

# parse_webmin_log(user, script, action, type, object, &params)
# Converts a logged action into a human-readable description
sub parse_webmin_log
{
my ($user, $script, $action, $type, $object, $p) = @_;
return &text("log_${action}_${type}", "<tt>".&html_escape($object)."</tt>");
}

1;
