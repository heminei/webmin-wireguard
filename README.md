# Webmin WireGuard

[![Release](https://img.shields.io/github/v/release/heminei/webmin-wireguard)](https://github.com/heminei/webmin-wireguard/releases/latest)
[![Build](https://img.shields.io/github/actions/workflow/status/heminei/webmin-wireguard/release.yml)](https://github.com/heminei/webmin-wireguard/actions)
[![License](https://img.shields.io/github/license/heminei/webmin-wireguard)](LICENSE)

Manage WireGuard VPN servers from Webmin and Virtualmin, with a dashboard in the style of [WGDashboard](https://github.com/donaldzou/WGDashboard).

The module edits the standard `/etc/wireguard/<interface>.conf` files directly and applies changes with `wg` and `wg-quick`. There is no separate database, and everything stays usable from the command line.

## Features

- **Interfaces**: create, edit, delete, start, stop, restart and reload; start at boot; edit the raw config file; import an existing wg-quick config.
- **Peers**: add one or many, edit, enable, disable and delete. Keys, optional preshared keys and the next free IPv4 address are generated for you. Each peer has its own client settings (allowed IPs, DNS, endpoint, keepalive, MTU).
- **Client configs**: show, copy, download as `.conf`, or scan as a QR code (generated in the browser, no extra packages needed).
- **Live status**: online state, last handshake, endpoint and transfer counters, refreshed every few seconds.
- **Traffic statistics**: history charts for an interface or a single peer over 1 hour, 24 hours, 7 days or 30 days.
- **Network map**: a diagram of which peer routes which network, including site-to-site networks behind a peer, with warnings for overlapping addresses and routes.
- **Backup and restore**: download all configs as a `.tar.gz`, restore from an upload, and keep automatic saved copies before every change or deletion.
- **Built in help**: a help page for every option. Available in English and Bulgarian.

## Requirements

- Linux with Webmin 2.x. Tested with Webmin 2.670 and Virtualmin on Debian 12, using the Authentic theme.
- `wireguard-tools` (`wg` and `wg-quick`).
- `tar`, for backups and restores. `systemctl` is needed only for the start-at-boot toggle.

Other Webmin themes should work, but the action buttons in the page header are designed for Authentic.

## Install

In Webmin open **Webmin > Webmin Configuration > Webmin Modules > Install Module**, choose **From ftp or http URL** and enter:

```
https://github.com/heminei/webmin-wireguard/releases/latest/download/wireguard.wbm.gz
```

The module appears under **Networking > WireGuard VPN**. Open it once after installing, because that registers the statistics collector.

Other ways to install:

- Download `wireguard.wbm.gz` from the [releases page](https://github.com/heminei/webmin-wireguard/releases) and upload it on the same Webmin page.
- Build the package yourself with `./package.sh` and upload it.
- Copy the repository to the Webmin directory as `wireguard`, make the CGIs executable and use **Refresh Modules**:

  ```bash
  rsync -av --exclude=.git ./ root@server:/usr/share/webmin/wireguard/   # /usr/libexec/webmin on RHEL
  ```

### Upgrade

Install the new package over the old one. Module settings, interfaces, saved copies and statistics are kept.

### Uninstall

Delete the module under **Webmin Configuration > Webmin Modules**. This removes the statistics collector. Your `/etc/wireguard` configs and running interfaces are not touched. Saved copies and statistics under `/var/webmin/modules/wireguard/` stay on disk until you delete them.

## Quick start

1. **Add a new interface** (or **Import interface config**) and start it.
2. Open the UDP listen port in the server firewall.
3. Open the interface and **Add a new peer**.
4. Open the peer's **Client config** to copy the config, download it, or scan the QR code with the WireGuard app.

Client allowed IPs default to the interface subnet, so clients only send VPN traffic through the tunnel. Set `0.0.0.0/0, ::/0` on a peer to route all of that client's traffic.

### Connect a router or another server (site-to-site)

Add the network behind the peer to the peer's **Allowed IPs**, for example `10.0.0.4/32, 192.168.10.0/24`, and add it to the **Client allowed IPs** of the clients that need it. The **Network map** shows who routes what.

To connect a second server that also runs this module, create the peer on the first server, download its client config, and use **Import interface config** on the second one.

## Configuration

- **Module Config** (the gear icon): command paths and the WireGuard config directory.
- **Default settings**: defaults for new peers (endpoint, DNS, keepalive, MTU), statistics collection, and how many saved copies to keep.

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
- Peer changes on a running interface use `wg syncconf`, so connected peers stay up. Interface changes restart it.
- Statistics are raw counters in `/var/webmin/modules/wireguard/stats/`, and saved copies are in `/var/webmin/modules/wireguard/backups/`.

## Security notes

- Interface configs can contain `PreUp`, `PostUp`, `PreDown` and `PostDown` commands that run as root. Only import or restore configs you trust.
- Backups and saved copies contain private keys. Store them securely.
- A client's allowed IPs only control what the client sends through the tunnel. To restrict what a peer can reach, add firewall rules on the server, for example in `PostUp` and `PostDown`.
- To report a vulnerability, please use a private [security advisory](https://github.com/heminei/webmin-wireguard/security/advisories/new) instead of a public issue.

## Troubleshooting

- **The module is not in the menu**: use **Webmin > Refresh Modules**, and check that `wg` and `wg-quick` are installed.
- **A peer never shows as online**: check that the listen port is open in the firewall, and that the server endpoint in the client config is reachable from the client.
- **Charts are empty**: open the module once so the collector is registered, then wait for a few intervals. Check that collection is on under **Default settings**.
- **Page errors**: see `/var/webmin/miniserv.error`.

## Contributing

Issues and pull requests are welcome at [github.com/heminei/webmin-wireguard](https://github.com/heminei/webmin-wireguard/issues).

There is no Webmin on a typical development machine. Syntax-check with a stub `WebminCore.pm` on `@INC`:

```bash
perl -I/tmp/stub -c index.cgi
```

See [AGENTS.md](AGENTS.md) for the layout, conventions and testing notes. New text goes in `lang/en`, with a matching Bulgarian string in `lang/bg` and a help page for every new option.

To publish a release, set `version=` in `module.info`, then push a matching tag (`git tag v1.1 && git push origin v1.1`). GitHub Actions builds `wireguard.wbm.gz` and attaches it to the release.

## License

BSD 3-Clause. See [LICENSE](LICENSE).

## Third-party code

`qrcode.js` is [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 by Kazuhiko Arase, under the MIT license.
