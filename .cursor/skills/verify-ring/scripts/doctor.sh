#!/usr/bin/env bash
# Read-only check: is this Ring instance worth driving?
#
# Usage:
#   bash .cursor/skills/verify-ring/scripts/doctor.sh
#
# Runs dev_util/cloud-health.sh, compares GET /api/v1/version (nginx) to
# git rev-parse HEAD, and confirms the seeded user can still obtain a token.
# Does not print the token. Retries the version read to absorb the 15s
# in-process cache in ring/lib/version_info.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cd "${REPO_ROOT}"
load_state

errors=0
note() {
  printf '%s\n' "$1"
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  errors=$((errors + 1))
}

if bash "${REPO_ROOT}/dev_util/cloud-health.sh"; then
  note "OK  cloud-health"
else
  fail "cloud-health"
fi

if [[ "${STARTED_VITE}" == "1" ]]; then
  if pid_alive "${VITE_PID}"; then
    note "OK  Vite pid ${VITE_PID} (started by this run)"
  else
    fail "Vite pid ${VITE_PID} is not alive"
  fi
else
  note "OK  Vite was already running; doctor will not treat it as owned"
fi

expected="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
actual=""
source_name=""
version_file="${STATE_DIR}/version.json"
mkdir -p "${STATE_DIR}"
for _attempt in 1 2 3 4 5; do
  if "${SCRIPT_DIR}/api.sh" GET /version >"${version_file}"; then
    read -r actual source_name < <(
      python3 - "${version_file}" <<'PY'
import json
import sys

try:
    payload = json.load(open(sys.argv[1]))
except (OSError, json.JSONDecodeError):
    print("", "")
    raise SystemExit(0)
git = payload.get("git") or {}
print(git.get("sha") or "", git.get("source") or "")
PY
    )
    if [[ "${actual}" == "${expected}" ]]; then
      break
    fi
  fi
  sleep 4
done
rm -f "${version_file}"

if [[ "${actual}" == "${expected}" ]]; then
  note "OK  version git.sha matches HEAD (${expected}) source=${source_name}"
else
  fail "version git.sha (${actual:-missing}) != HEAD (${expected}) source=${source_name:-missing}"
fi

login_file="${STATE_DIR}/doctor-login.json"
login_code="$(
  curl -sk -o "${login_file}" -w '%{http_code}' \
    -X POST "https://localhost/api/v1/login/access-token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${SEEDED_EMAIL}&password=${SEEDED_PASSWORD}"
)"
if [[ "${login_code}" == "200" ]] && python3 - "${login_file}" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1]))
token = payload.get("access_token") or ""
raise SystemExit(0 if payload.get("token_type") == "bearer" and len(token) >= 20 else 1)
PY
then
  note "OK  seeded login via nginx returned a bearer token"
else
  fail "seeded login via nginx (HTTP ${login_code})"
fi
rm -f "${login_file}"

if [[ -n "${EVIDENCE_DIR}" ]]; then
  mkdir -p "${EVIDENCE_DIR}"
  {
    echo "expected_sha=${expected}"
    echo "actual_sha=${actual}"
    echo "source=${source_name}"
    echo "errors=${errors}"
  } >"${EVIDENCE_DIR}/doctor.txt"
fi

if [[ "${errors}" -eq 0 ]]; then
  note "verify-ring doctor passed"
  exit 0
fi
echo "${errors} doctor check(s) failed" >&2
exit 1
