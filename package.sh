#!/bin/bash
# Builds wireguard.wbm.gz, installable via Webmin > Webmin Modules
set -euo pipefail

cd "$(dirname "$0")"
version=$(sed -n 's/^version=//p' module.info)
out="${1:-wireguard-$version.wbm.gz}"

tar czf "$out" \
	--exclude=.git --exclude='*.wbm.gz' --exclude=package.sh \
	--transform 's,^\.,wireguard,' \
	.

echo "Created $out"
