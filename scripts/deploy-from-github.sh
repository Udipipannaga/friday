#!/usr/bin/env bash
set -euo pipefail

# Run on the FRIDAY VPS with a reviewed 40-character commit SHA.
if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo 'Usage: deploy-from-github.sh <40-character GitHub commit SHA>' >&2
  exit 2
fi
expected_commit="$1"
source_dir=/opt/friday-source
release_dir="/opt/friday-releases/${expected_commit}"
secrets_file=/opt/friday/.env

if [[ ! -f "$secrets_file" ]]; then
  echo "Missing protected runtime environment file: $secrets_file" >&2
  exit 1
fi

if [[ ! -d "$source_dir/.git" ]]; then
  git clone --depth=1 --no-checkout https://github.com/Udipipannaga/friday.git "$source_dir"
fi
git -C "$source_dir" fetch --depth=1 origin main
actual_commit="$(git -C "$source_dir" rev-parse FETCH_HEAD)"
if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "GitHub main is ${actual_commit}; expected ${expected_commit}. Deployment cancelled." >&2
  exit 1
fi

if [[ ! -d "$release_dir" ]]; then
  mkdir -p "$release_dir"
  git -C "$source_dir" archive "$actual_commit" | tar -xf - -C "$release_dir"
fi
ln -sfn "$secrets_file" "$release_dir/.env"
cd "$release_dir"
docker compose config --quiet
docker compose build
docker compose up -d --no-build
curl --fail --silent --show-error --retry 15 --retry-all-errors --retry-delay 2 \
  --resolve friday.srv2033118.hstgr.cloud:443:127.0.0.1 \
  https://friday.srv2033118.hstgr.cloud/api/health
echo
echo "FRIDAY deployed from GitHub commit ${actual_commit}"
