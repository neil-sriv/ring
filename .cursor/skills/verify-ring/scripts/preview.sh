#!/usr/bin/env bash
# Build the React app and serve vite preview on http://127.0.0.1:4173.
#
# Usage:
#   bash .cursor/skills/verify-ring/scripts/preview.sh
#
# This only starts the preview server. A curl of the HTML shell is not the
# blank-page check. Open /login in a browser and follow the Preview section
# of SKILL.md. Cleanup stops this server when the run started it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cd "${REPO_ROOT}"
load_state

if [[ -z "${RUN_ID}" || -z "${EVIDENCE_DIR}" ]]; then
  echo "Run launch.sh first so preview evidence has a run directory." >&2
  exit 1
fi

if [[ "${STARTED_PREVIEW}" == "1" ]] && pid_alive "${PREVIEW_PID}"; then
  echo "Preview is already running (pid ${PREVIEW_PID})." >&2
  exit 1
fi
if tmx has-session -t "${PREVIEW_SESSION}" 2>/dev/null; then
  echo "tmux session ${PREVIEW_SESSION} already exists. Run cleanup.sh first." >&2
  exit 1
fi

if curl -sf -o /dev/null "http://127.0.0.1:4173/"; then
  echo "Something is already serving :4173. verify-ring will not kill it by name." >&2
  exit 1
fi

# Nginx bind-mounts react/dist. If that directory was created by root before
# a build existed, pnpm cannot write sw.mjs (EACCES) and the blank-page check
# never starts. Take ownership of the output dir, then build.
dist_dir="${REPO_ROOT}/react/dist"
if [[ -d "${dist_dir}" && ! -w "${dist_dir}" ]]; then
  echo "react/dist is not writable; chown to the current user"
  sudo chown -R "$(id -u):$(id -g)" "${dist_dir}"
fi

echo "Building react/ with VITE_API_URL empty and SW_DEV=false"
(
  cd "${REPO_ROOT}/react"
  VITE_API_URL="" SW_DEV=false pnpm run build
)

tmx new-session -d -s "${PREVIEW_SESSION}" -c "${REPO_ROOT}/react" -- \
  env VITE_API_URL="" SW_DEV=false pnpm exec vite preview --host 127.0.0.1 --port 4173 --strictPort
PREVIEW_PID="$(tmx list-panes -t "${PREVIEW_SESSION}" -F '#{pane_pid}')"
STARTED_PREVIEW=1
save_state

ready=0
for _attempt in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:4173/login" | grep -q 'id="root"'; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "${ready}" != "1" ]]; then
  echo "vite preview did not serve /login" >&2
  exit 1
fi

mkdir -p "${EVIDENCE_DIR}/preview"
cat >"${EVIDENCE_DIR}/preview/server.txt" <<EOF
url=http://127.0.0.1:4173/login
pid=${PREVIEW_PID}
note=HTML shell is up. The blank-page check is the browser, not this file.
EOF

cat <<EOF
Preview is serving http://127.0.0.1:4173/login (pid ${PREVIEW_PID}).
The HTML shell being present is not a pass. Open that URL in a browser and
confirm the login page rendered. See SKILL.md → Preview.
vite preview does not proxy /api/v1 (the proxy is on the dev server only).
A failed login on :4173 is not a blank page.
EOF
