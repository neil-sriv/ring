#!/usr/bin/env bash
# Idempotent dev seed: test user for cloud/local browser testing.
set -euo pipefail

API_BASE="${1:-http://localhost:8001}"
EMAIL="${CLOUD_TEST_EMAIL:-test@example.com}"
PASSWORD="${CLOUD_TEST_PASSWORD:-testpassword123}"
NAME="${CLOUD_TEST_NAME:-Test User}"

response="$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/v1/parties/user" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"${NAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")"

body="${response%$'\n'*}"
status="${response##*$'\n'}"

case "$status" in
  201)
    echo "Seeded test user ${EMAIL}"
    ;;
  400)
    if [[ "$body" == *"already registered"* ]]; then
      echo "Test user ${EMAIL} already exists"
    else
      echo "Seed skipped (${status}): ${body}" >&2
      exit 1
    fi
    ;;
  *)
    echo "Seed failed (${status}): ${body}" >&2
    exit 1
    ;;
esac
