#!/bin/bash
# Builds wireguard.wbm.gz, installable via Webmin > Webmin Modules
set -euo pipefail

version=$(sed -n 's/^version=//p' "$(dirname "$0")/module.info")
out="$(realpath -m "${1:-wireguard-$version.wbm.gz}")"
cd "$(dirname "$0")"

# Write outside the source tree, or tar sees the archive change while reading it
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

tar czf "$tmp/package.tgz" \
	--exclude=.git --exclude=.github --exclude='*.wbm.gz' --exclude=package.sh \
	--transform 's,^\.,wireguard,' \
	.
mv "$tmp/package.tgz" "$out"

echo "Created $out"
