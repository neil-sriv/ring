#!/usr/bin/env bash
# Exit 0 when Ring cloud dev stack is ready for browser testing.
set -euo pipefail

errors=0

check() {
  local label="$1"
  shift
  if "$@"; then
    echo "OK  ${label}"
  else
    echo "FAIL ${label}" >&2
    errors=$((errors + 1))
  fi
}

check_cockroach() {
  sudo docker exec ring-cockroach ./cockroach sql \
    --certs-dir=/root/.cockroach-certs \
    -d ring \
    -e "SELECT 1" >/dev/null 2>&1
}

check_api() {
  curl -sf "http://localhost:8001/api/v1/openapi.json" >/dev/null
}

check_vite() {
  curl -sf "http://localhost:5173/" >/dev/null
}

check_nginx_api() {
  curl -skf "https://localhost/api/v1/openapi.json" >/dev/null
}

check "CockroachDB" check_cockroach
check "API :8001" check_api
check "Vite :5173" check_vite
check "Nginx API :443" check_nginx_api

if [[ "$errors" -eq 0 ]]; then
  echo "Ring cloud stack is healthy"
  exit 0
fi

echo "${errors} check(s) failed" >&2
exit 1
