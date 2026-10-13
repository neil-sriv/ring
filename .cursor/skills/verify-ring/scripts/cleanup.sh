#!/usr/bin/env bash
# Stop only the processes and the compose stack this verify-ring run started.
#
# Usage:
#   bash .cursor/skills/verify-ring/scripts/cleanup.sh
#
# Does not delete /opt/cursor/artifacts/verify-ring. Does not kill by process
# name. A second run is a no-op when nothing is recorded.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cd "${REPO_ROOT}"
load_state

evidence="${EVIDENCE_DIR}"

if [[ "${STARTED_VITE}" == "1" ]]; then
  if tmx has-session -t "${VITE_SESSION}" 2>/dev/null; then
    tmx kill-session -t "${VITE_SESSION}"
    echo "Stopped Vite session ${VITE_SESSION}"
  elif pid_alive "${VITE_PID}"; then
    kill "${VITE_PID}"
    echo "Stopped Vite pid ${VITE_PID}"
  else
    echo "Vite session was already gone"
  fi
else
  echo "Leaving Vite alone (this run did not start it)"
fi

if [[ "${STARTED_PREVIEW}" == "1" ]]; then
  if tmx has-session -t "${PREVIEW_SESSION}" 2>/dev/null; then
    tmx kill-session -t "${PREVIEW_SESSION}"
    echo "Stopped preview session ${PREVIEW_SESSION}"
  elif pid_alive "${PREVIEW_PID}"; then
    kill "${PREVIEW_PID}"
    echo "Stopped preview pid ${PREVIEW_PID}"
  else
    echo "Preview session was already gone"
  fi
else
  echo "Leaving preview alone (this run did not start it)"
fi

if [[ "${STARTED_COMPOSE}" == "1" ]]; then
  sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev down
  echo "Stopped the compose stack this run started"
else
  echo "Leaving compose alone (this run did not start it)"
fi

rm -f \
  "${STATE_FILE}" \
  "${STATE_DIR}/login-probe.json" \
  "${STATE_DIR}/doctor-login.json" \
  "${STATE_DIR}/version.json" \
  "${STATE_DIR}/owner-login.json" \
  "${STATE_DIR}/outsider-login.json" \
  "${STATE_DIR}/owner.token" \
  "${STATE_DIR}/outsider.token"

if [[ -n "${evidence}" ]]; then
  if [[ -d "${evidence}" ]]; then
    echo "Evidence kept at ${evidence}"
  else
    echo "Evidence directory is missing: ${evidence}" >&2
    exit 1
  fi
else
  echo "No evidence directory was recorded"
fi
