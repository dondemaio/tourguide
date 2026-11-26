#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
data_dir="$repo_dir/data"
destination="$data_dir/switzerland-latest.osm.pbf"
url="https://download.geofabrik.de/europe/switzerland-latest.osm.pbf"

mkdir -p "$data_dir"
temporary_file="$(mktemp "$data_dir/.switzerland-latest.osm.pbf.XXXXXX")"
trap 'rm -f -- "$temporary_file"' EXIT

curl --fail --location --retry 3 --output "$temporary_file" "$url"
mv -f -- "$temporary_file" "$destination"

printf 'Downloaded %s\n' "$destination"
