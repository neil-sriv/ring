#!/usr/bin/env bash
# Idempotent dev seed: test user + sample group/letter for cloud/local browser testing.
#
# After bootstrap, agents can log in and immediately exercise groups, loops, and
# unanswered-question UI instead of starting from an empty dashboard.
set -euo pipefail

API_BASE="${1:-http://localhost:8001}"
EMAIL="${CLOUD_TEST_EMAIL:-test@example.com}"
PASSWORD="${CLOUD_TEST_PASSWORD:-testpassword123}"
NAME="${CLOUD_TEST_NAME:-Test User}"
GROUP_NAME="${CLOUD_SEED_GROUP_NAME:-Cloud Seed Group}"
# Days until the seeded upcoming letter's send_at.
LETTER_SEND_IN_DAYS="${CLOUD_SEED_LETTER_SEND_IN_DAYS:-14}"

json_field() {
  local json="$1"
  local field="$2"
  python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$field" <<<"$json"
}

http_json() {
  # Usage: http_json METHOD URL [curl args...]
  # Prints "STATUS\nBODY" on stdout. Does not exit on HTTP errors.
  local method="$1"
  local url="$2"
  shift 2
  local response
  response="$(curl -s -w "\n%{http_code}" -X "$method" "$url" "$@")"
  local status="${response##*$'\n'}"
  local body="${response%$'\n'*}"
  printf '%s\n%s' "$status" "$body"
}

seed_user() {
  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json POST "${API_BASE}/api/v1/parties/user" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${NAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

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
}

login() {
  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json POST "${API_BASE}/api/v1/login/access-token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}")

  if [[ "$status" != "200" ]]; then
    echo "Login failed (${status}): ${body}" >&2
    exit 1
  fi
  json_field "$body" access_token
}

read_me() {
  local token="$1"
  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json GET "${API_BASE}/api/v1/parties/me" \
    -H "Authorization: Bearer ${token}")

  if [[ "$status" != "200" ]]; then
    echo "GET /parties/me failed (${status}): ${body}" >&2
    exit 1
  fi
  printf '%s' "$body"
}

find_seed_group_id() {
  local token="$1"
  local user_api_id="$2"
  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json GET \
    "${API_BASE}/api/v1/parties/groups/?user_api_id=${user_api_id}" \
    -H "Authorization: Bearer ${token}")

  if [[ "$status" != "200" ]]; then
    echo "List groups failed (${status}): ${body}" >&2
    exit 1
  fi

  python3 -c '
import json, sys
name = sys.argv[1]
groups = json.load(sys.stdin)
for g in groups:
    if g.get("name") == name:
        print(g["api_identifier"])
        break
' "$GROUP_NAME" <<<"$body"
}

create_seed_group() {
  local token="$1"
  local user_api_id="$2"
  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json POST "${API_BASE}/api/v1/parties/group" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${GROUP_NAME}\",\"admin_api_identifier\":\"${user_api_id}\"}")

  if [[ "$status" != "201" ]]; then
    echo "Create group failed (${status}): ${body}" >&2
    exit 1
  fi
  json_field "$body" api_identifier
}

group_has_live_letter() {
  local token="$1"
  local group_api_id="$2"
  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json GET \
    "${API_BASE}/api/v1/letters/letters/?group_api_id=${group_api_id}" \
    -H "Authorization: Bearer ${token}")

  if [[ "$status" != "200" ]]; then
    echo "List letters failed (${status}): ${body}" >&2
    exit 1
  fi

  python3 -c '
import json, sys
letters = json.load(sys.stdin)
live = {"UPCOMING", "IN_PROGRESS"}
print("yes" if any(l.get("status") in live for l in letters) else "no")
' <<<"$body"
}

create_seed_letter() {
  local token="$1"
  local group_api_id="$2"
  local send_at
  send_at="$(python3 -c '
from datetime import datetime, timedelta, timezone
import os
days = int(os.environ["LETTER_SEND_IN_DAYS"])
print((datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ"))
')"

  local status body
  {
    read -r status
    body="$(cat)"
  } < <(http_json POST "${API_BASE}/api/v1/letters/letter" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d "{\"group_api_identifier\":\"${group_api_id}\",\"send_at\":\"${send_at}\"}")

  if [[ "$status" != "200" && "$status" != "201" ]]; then
    echo "Create letter failed (${status}): ${body}" >&2
    exit 1
  fi
  json_field "$body" api_identifier
}

seed_sample_group() {
  local token user_json user_api_id group_api_id

  token="$(login)"
  user_json="$(read_me "$token")"
  user_api_id="$(json_field "$user_json" api_identifier)"

  group_api_id="$(find_seed_group_id "$token" "$user_api_id")"
  if [[ -z "$group_api_id" ]]; then
    group_api_id="$(create_seed_group "$token" "$user_api_id")"
    echo "Seeded sample group ${GROUP_NAME} (${group_api_id})"
  else
    echo "Sample group ${GROUP_NAME} already exists (${group_api_id})"
  fi

  if [[ "$(group_has_live_letter "$token" "$group_api_id")" == "yes" ]]; then
    echo "Sample group already has an upcoming/in-progress letter"
    return 0
  fi

  local letter_api_id
  letter_api_id="$(create_seed_letter "$token" "$group_api_id")"
  echo "Seeded upcoming letter ${letter_api_id} (send in ${LETTER_SEND_IN_DAYS}d)"
}

export LETTER_SEND_IN_DAYS

seed_user
seed_sample_group
