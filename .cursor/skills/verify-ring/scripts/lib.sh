#!/usr/bin/env bash
# Shared paths for the verify-ring scripts. Source this file; do not execute it.
# Usage: source .cursor/skills/verify-ring/scripts/lib.sh
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "Source this file from the other verify-ring scripts. It is not a command." >&2
  echo "Usage: source .cursor/skills/verify-ring/scripts/lib.sh" >&2
  exit 2
fi

VERIFY_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${VERIFY_SCRIPT_DIR}/../../../.." && pwd)"
STATE_DIR="/tmp/verify-ring"
STATE_FILE="${STATE_DIR}/state.env"
EVIDENCE_ROOT="/opt/cursor/artifacts/verify-ring"
VITE_SESSION="verify-ring-vite"
PREVIEW_SESSION="verify-ring-preview"
SEEDED_EMAIL="${CLOUD_TEST_EMAIL:-test@example.com}"
SEEDED_PASSWORD="${CLOUD_TEST_PASSWORD:-testpassword123}"

tmx() {
  if [[ -f /exec-daemon/tmux.portal.conf ]]; then
    tmux -f /exec-daemon/tmux.portal.conf "$@"
  else
    tmux "$@"
  fi
}

load_state() {
  RUN_ID=""
  EVIDENCE_DIR=""
  STARTED_COMPOSE=0
  STARTED_VITE=0
  STARTED_PREVIEW=0
  VITE_PID=""
  PREVIEW_PID=""
  if [[ -f "${STATE_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${STATE_FILE}"
  fi
}

save_state() {
  mkdir -p "${STATE_DIR}"
  cat >"${STATE_FILE}" <<EOF
RUN_ID=${RUN_ID}
EVIDENCE_DIR=${EVIDENCE_DIR}
STARTED_COMPOSE=${STARTED_COMPOSE}
STARTED_VITE=${STARTED_VITE}
STARTED_PREVIEW=${STARTED_PREVIEW}
VITE_PID=${VITE_PID}
PREVIEW_PID=${PREVIEW_PID}
EOF
  chmod 600 "${STATE_FILE}"
}

pid_alive() {
  local pid="${1:-}"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

compose_api_up() {
  sudo docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'ring-api'
}

ensure_docker() {
  if sudo docker info >/dev/null 2>&1; then
    return 0
  fi
  echo "Docker daemon is not up; starting it (sudo service docker start)"
  sudo service docker start
  local attempt
  for attempt in $(seq 1 30); do
    if sudo docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "Docker daemon did not become ready" >&2
  return 1
}
