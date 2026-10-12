# AGENTS.md

Webmin module for managing WireGuard (WGDashboard-style). Perl CGIs plus small vanilla JS. The repo root is the module directory; it installs as `wireguard` under the Webmin directory.

## Layout

- `wireguard-lib.pl`: all shared logic (config parser/writer, `wg`/`wg-quick` wrappers, status, IP allocation, client config, statistics, JSON helpers). Every CGI does `require './wireguard-lib.pl'`.
- `*.cgi`: pages. `index` (interface list), `view_iface` (status + peers), `edit_iface`/`save_iface`/`action_iface` (reload, boot toggle) plus `start`/`stop`/`restart`/`delete_iface`, `edit_config`/`save_config` (raw config editor), `edit_import`/`save_import` (import a wg-quick config as a new interface), `edit_peer`/`save_peer`/`action_peer`, `show_peer`/`download_peer` (client config + QR), `stats`/`stats_data` (charts + JSON), `edit_defaults`/`save_defaults`, `network_map` (SVG diagram of who routes which network, plus overlap warnings), `backup`/`download_backup`/`restore_backup`/`snapshot_action` (backup, restore, saved copies).
- `lang/en`: all UI text. `help/*.html`: one help page per option, linked with `&hlink($text{'key'}, 'key')`. Bulgarian translations live in `lang/bg`, `help/*.bg.html`, `config.info.bg` and `desc_bg`/`longdesc_bg` in `module.info`; keep them in step with the English files.
- `wg-live.js`, `wg-chart.js`, `qrcode.js` (MIT, qrcode-generator 1.4.4): static JS served from the module directory.
- `config`, `config.info`: module settings. `log_parser.pl`, `install_check.pl`, `uninstall.pl` (removes the stats collector), `module.info`.
- `package.sh`: builds `wireguard-<version>.wbm.gz` for Webmin's module installer.

## Conventions

- Webmin style: tab indentation, `&function()` calls, `%text` strings from `lang/en` (add every new string there), `&error()` / `&error_setup()` for failures, `&webmin_log()` with a matching `log_<action>_<type>` string in `lang/en`.
- New CGIs must be executable (`chmod +x`) and start with `#!/usr/bin/perl`.
- Validate all user input with the `valid_*` helpers before it reaches a config file or command. Quote shell arguments with `quotemeta`. Strip newlines with `clean_value`.
- Keep `lib` functions free of `my` file-level state that CGIs depend on; pass `$conf` explicitly to subs.
- Inline page scripts that depend on a bundled JS file must use `&load_script_then()`, because the Authentic theme injects page scripts asynchronously.
- Add a help page and `hlink` for every new form option.
- Follow the Webmin UX style: header right-side buttons go through `&header_links()` (the `$rightside` argument of `ui_print_header`), but the Authentic theme only turns links into icon buttons when the script name matches `start.cgi`, `stop.cgi`, `restart.cgi`, `apply.cgi`, `delete_*` or `config.cgi`. Use those names for header actions, keep all other links in the page body, and show the wireguard-tools version as the index header subtitle.

## Data format

- Config files are `/etc/wireguard/<iface>.conf`, written mode 0600.
- Peer metadata is stored as `# Key = value` comments inside `[Peer]` (`Name`, `Notes`, `PrivateKey`, `ClientDNS`, `ClientAllowedIPs`, `ClientEndpoint`, `ClientKeepalive`, `ClientMTU`). `wg-quick` ignores them.
- Disabled peers are the whole `[Peer]` block with each line prefixed `#DISABLED#`.
- Client private keys are stored in the peer comment so the client config and QR can be rebuilt.
- Client allowed IPs default to the interface subnet(s) (`iface_subnets`).
- Running interfaces are changed with `wg syncconf` (peer edits) or restart (interface edits).
- Statistics: `collect_stats` runs from webmincron (registered by `ensure_collector_job`, called from the index page) and appends raw counters to `$module_var_directory/stats/<iface>.log` (`time pubkey rx tx handshake`). Deltas and counter resets are handled at read time in `get_stats_series`.
- Backups: `write_wg_conf` and interface deletion call `snapshot_conf`, which saves the old file to `$module_var_directory/backups/<iface>/<epoch>.conf` (newest `backup_keep` kept). Uploaded archives go through `restore_archive`, which accepts only plain `<iface>.conf` files and snapshots what it overwrites.

## Development and testing

- There is no Webmin on the dev machine. Syntax-check with a stub `WebminCore.pm` on `@INC`: `perl -I/tmp/stub -c file.cgi`. The stub must export the Webmin functions the file calls.
- Parser logic can be exercised by requiring `wireguard-lib.pl` with stubs for `read_file_lines`, `open_lock_tempfile`, `print_tempfile`, `close_tempfile` (assign them after the `require`, since the stub import overwrites earlier definitions).
- Test on a real server (Debian/Virtualmin, Webmin 2.x): rsync the folder to `/usr/share/webmin/wireguard/` (`/usr/libexec/webmin/` on RHEL), or upload the package under Webmin Modules.
- Build a package with `./package.sh [output]`.
