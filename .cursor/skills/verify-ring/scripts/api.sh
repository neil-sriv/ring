#!/usr/bin/env bash
# Call Ring through the nginx TLS proxy. The certificate is the local
# self-signed cert from dev_util/ssl.sh, so curl uses -k.
#
# Usage:
#   api.sh METHOD /path [curl args...]
#
# Examples:
#   api.sh GET /version
#   api.sh POST /login/access-token \
#     -H 'Content-Type: application/x-www-form-urlencoded' \
#     -d 'username=test@example.com&password=testpassword123'
#
# /path is appended to https://localhost/api/v1. Do not include the /api/v1 prefix.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: api.sh METHOD /path [curl args...]" >&2
  exit 2
fi

method="$1"
path="$2"
shift 2

case "${path}" in
  /*) ;;
  *)
    echo "path must start with / (got: ${path})" >&2
    exit 2
    ;;
esac

exec curl -skS -X "${method}" "https://localhost/api/v1${path}" "$@"
