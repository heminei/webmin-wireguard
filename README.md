# Webmin WireGuard

A Webmin module for managing WireGuard VPN servers, in the style of WGDashboard. It edits the standard `/etc/wireguard/<interface>.conf` files directly and applies changes with `wg` and `wg-quick`, so everything stays usable from the command line.

## Features

- **Interfaces**: create, edit, delete, start, stop, restart and reload; start at boot (`wg-quick@<name>`); edit the raw config file; import an existing wg-quick config.
- **Peers**: add (one or many), edit, enable, disable and delete; automatic key generation, optional preshared keys and the next free IPv4 address; per-peer client settings (allowed IPs, DNS, endpoint, keepalive, MTU).
- **Client configs**: show, copy, download as `.conf` and scan as a QR code (generated in the browser).
- **Live status**: online state, last handshake, endpoint and transfer counters, refreshed every few seconds.
- **Traffic statistics**: history charts for an interface or a single peer over 1 hour, 24 hours, 7 days or 30 days, collected by a Webmin scheduled job.
- **Network map**: a diagram of which peer routes which network (including site-to-site networks behind a peer), with warnings for overlapping addresses and routes.
- **Backup and restore**: download all configs as a `.tar.gz`, restore from an upload, and automatic saved copies before every change or deletion.
- **Help and translations**: a help page for every option; English and Bulgarian.

## Requirements

- Webmin 2.x (developed against the Authentic theme) on Linux.
- `wireguard-tools` (`wg` and `wg-quick`). `systemctl` is needed only for the start-at-boot toggle.
- `tar`, for backups and restores.

## Install

Install the latest release straight from GitHub: in Webmin open **Webmin > Webmin Configuration > Webmin Modules > Install Module**, choose **From ftp or http URL** and enter:

```
https://github.com/heminei/webmin-wireguard/releases/latest/download/wireguard.wbm.gz
```

To release a new version, set `version=` in `module.info`, then push a matching tag (`git tag v1.1 && git push origin v1.1`). The GitHub Actions workflow builds `wireguard.wbm.gz` and attaches it to the release.

Or build a package and upload it under the same page:

```bash
./package.sh                 # creates wireguard-<version>.wbm.gz
./package.sh /tmp/wg.wbm.gz  # or choose the output path
```

Or copy the repository to the Webmin directory as `wireguard`, make the CGIs executable and use **Refresh Modules**:

```bash
rsync -av --exclude=.git ./ root@server:/usr/share/webmin/wireguard/   # /usr/libexec/webmin on RHEL
```

The module appears under **Networking > WireGuard VPN**. Open it once after installing: this registers the statistics collector.

## Usage

1. **Add a new interface** (or **Import interface config**) and start it.
2. Open the interface and **Add a new peer**. Open the UDP listen port in the server firewall.
3. Open the peer's **Client config** to copy the config, download it, or scan the QR code.
4. To give a peer access to a network behind it (for example a router), add that network to the peer's **Allowed IPs**, and add it to the **Client allowed IPs** of the clients that need it. The **Network map** shows the result.

Client allowed IPs default to the interface subnet, so clients only send VPN traffic through the tunnel. Use `0.0.0.0/0, ::/0` to route all of a client's traffic.

Module settings (command paths, config directory) are under the standard **Module Config** page. Defaults for new peers and statistics are under **Default settings**.

## How data is stored

- Configs are `/etc/wireguard/<interface>.conf`, mode 0600. Peer names, notes and client settings are comments inside each `[Peer]` section, so `wg-quick` ignores them:

  ```
  [Peer]
  # Name = alice
  # PrivateKey = <client private key>
  PublicKey = ...
  AllowedIPs = 10.0.0.2/32
  ```

- Disabled peers keep their whole block, with every line prefixed `#DISABLED#`.
- Client private keys are stored in the peer comment so the client config and QR code can be rebuilt. Treat the config files and backups as secrets.
- Running interfaces are updated with `wg syncconf` for peer changes, and restarted for interface changes.
- Statistics are raw counters under `/var/webmin/modules/wireguard/stats/`; saved copies are under `/var/webmin/modules/wireguard/backups/`.

## Security notes

- Interface configs can contain `PreUp`, `PostUp`, `PreDown` and `PostDown` commands that run as root. Only import or restore configs you trust.
- A client's allowed IPs only control what the client sends through the tunnel. To restrict what a peer can reach, add firewall rules on the server (for example in `PostUp` and `PostDown`).

## Development

There is no Webmin on the development machine. Syntax-check with a stub `WebminCore.pm` on `@INC`:

```bash
perl -I/tmp/stub -c index.cgi
```

The config parser and helpers in `wireguard-lib.pl` can be tested by requiring the file with stubs for the Webmin functions they call. See [AGENTS.md](AGENTS.md) for the layout, conventions and testing notes.

## Third-party code

`qrcode.js` is [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 by Kazuhiko Arase, under the MIT license.
