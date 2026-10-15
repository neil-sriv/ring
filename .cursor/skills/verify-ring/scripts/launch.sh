#!/usr/bin/env bash
# Start Ring for verification and wait until a seeded user can log in.
#
# Usage:
#   bash .cursor/skills/verify-ring/scripts/launch.sh
#
# Ready means the seeded user receives a bearer token through nginx and Vite
# is serving the app module. The "=== Ring cloud ready ===" banner from
# cloud-start.sh --bootstrap-only is printed before Vite is up; this script
# does not stop there.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.ring-cloud-prod-db/mode" ]]; then
  echo "Refusing to launch: .ring-cloud-prod-db/mode is set." >&2
  echo "verify-ring runs alembic upgrade head against the local Docker database only." >&2
  exit 1
fi

mkdir -p "${STATE_DIR}"
load_state

if [[ "${STARTED_VITE}" == "1" ]] && pid_alive "${VITE_PID}"; then
  echo "verify-ring already owns Vite (pid ${VITE_PID}). Refusing a second instance." >&2
  exit 1
fi
if [[ "${STARTED_COMPOSE}" == "1" ]] && compose_api_up; then
  echo "verify-ring already owns the compose stack. Refusing a second instance." >&2
  exit 1
fi
if [[ "${STARTED_PREVIEW}" == "1" ]] && pid_alive "${PREVIEW_PID}"; then
  echo "verify-ring preview is still running (pid ${PREVIEW_PID}). Run cleanup.sh first." >&2
  exit 1
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_ID}"
mkdir -p "${EVIDENCE_DIR}"
STARTED_COMPOSE=0
STARTED_VITE=0
STARTED_PREVIEW=0
VITE_PID=""
PREVIEW_PID=""

ensure_docker

if compose_api_up; then
  STARTED_COMPOSE=0
  echo "Compose is already up; this run will not stop it during cleanup."
else
  STARTED_COMPOSE=1
fi
save_state

bash "${REPO_ROOT}/.cursor/cloud-start.sh" --bootstrap-only

if curl -sf -o /dev/null "http://localhost:5173/"; then
  STARTED_VITE=0
  echo "Vite is already serving :5173; this run will not stop it during cleanup."
else
  if tmx has-session -t "${VITE_SESSION}" 2>/dev/null; then
    echo "tmux session ${VITE_SESSION} already exists. Run cleanup.sh first." >&2
    exit 1
  fi
  STARTED_VITE=1
  tmx new-session -d -s "${VITE_SESSION}" -c "${REPO_ROOT}" -- \
    bash .cursor/cloud-start.sh --vite-only
  VITE_PID="$(tmx list-panes -t "${VITE_SESSION}" -F '#{pane_pid}')"
fi
save_state

login_ok() {
  local body_file code
  body_file="${STATE_DIR}/login-probe.json"
  code="$(
    curl -sk -o "${body_file}" -w '%{http_code}' \
      -X POST "https://localhost/api/v1/login/access-token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=${SEEDED_EMAIL}&password=${SEEDED_PASSWORD}"
  )"
  if [[ "${code}" != "200" ]]; then
    rm -f "${body_file}"
    return 1
  fi
  python3 - "${body_file}" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1]))
token = payload.get("access_token") or ""
if payload.get("token_type") != "bearer" or len(token) < 20:
    sys.exit(1)
PY
  rm -f "${body_file}"
}

echo "Waiting until the seeded user can log in and Vite is serving src/main.tsx"
ready=0
for _attempt in $(seq 1 60); do
  if bash "${REPO_ROOT}/dev_util/cloud-health.sh" >/tmp/verify-ring/health-last.txt 2>&1 \
    && curl -sf "http://localhost:5173/src/main.tsx" | grep -q "createRoot" \
    && login_ok; then
    ready=1
    break
  fi
  sleep 2
done

if [[ "${ready}" != "1" ]]; then
  echo "Ring did not become usable. Last health output:" >&2
  cat /tmp/verify-ring/health-last.txt >&2 || true
  exit 1
fi

cat >"${EVIDENCE_DIR}/launch.txt" <<EOF
run_id=${RUN_ID}
evidence_dir=${EVIDENCE_DIR}
app=http://localhost:5173
login=http://localhost:5173/login
api=https://localhost/api/v1/
seeded_email=${SEEDED_EMAIL}
started_compose=${STARTED_COMPOSE}
started_vite=${STARTED_VITE}
EOF

cat <<EOF

=== verify-ring ready ===
  Run:      ${RUN_ID}
  App:      http://localhost:5173/login
  API:      https://localhost/api/v1/
  Login:    ${SEEDED_EMAIL} / ${SEEDED_PASSWORD}
  Evidence: ${EVIDENCE_DIR}
  Doctor:   bash .cursor/skills/verify-ring/scripts/doctor.sh

Ready means a seeded login through nginx returned a bearer token and Vite
served src/main.tsx. The cloud-start banner alone is not ready.
EOF
