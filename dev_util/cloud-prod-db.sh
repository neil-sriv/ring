#!/usr/bin/env bash
# Switch the Cursor Cloud Agent stack between local Cockroach and Cockroach Cloud
# (prod or staging) so a local Vite frontend can exercise real data via the local API.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="${ROOT}/.ring-cloud-prod-db"
MARKER="${STATE_DIR}/mode"
ENV_BACKUP="${STATE_DIR}/.env.local-backup"
CA_PATH="${HOME}/.postgresql/root.crt"

COMPOSE_LOCAL=(sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev)
COMPOSE_PROD_DB=(
  sudo docker compose
  -f compose.core.yml
  -f compose.dev.yml
  -f compose.cloud-prod-db.yml
  --profile dev
)

LOCAL_COCKROACH_URI='cockroachdb://ringcockroach:ringcockroach@cockroach:26257/ring?sslmode=require'

usage() {
  cat <<'EOF'
Usage: bash dev_util/cloud-prod-db.sh <command> [options]

Commands:
  enable [--staging] [--yes]   Point local API at Cockroach Cloud; restart API
  disable                      Restore local Cockroach URI; restart API
  status                       Show current mode and secret/cert readiness
  health                       Verify API is up and can query the active DB

Secrets (Cursor Cloud Agent environment / dashboard):
  RING_PROD_COCKROACH_DATABASE_URI      required for `enable`
  RING_STAGING_COCKROACH_DATABASE_URI   required for `enable --staging`
  RING_COCKROACH_CA_CERT                PEM body for ~/.postgresql/root.crt

Egress: allow *.cockroachlabs.cloud (and the cluster SQL host if more specific).

Safety:
  - DISABLE_SCHEDULER=true is forced so APScheduler does not run against cloud DB
  - Never run `ring db upgrade` / alembic against prod from a cloud agent
  - Prefer staging; treat prod writes as live user data
EOF
}

require_env_file() {
  if [[ ! -f .env ]]; then
    echo "Missing .env — run bash .cursor/cloud-start.sh --bootstrap-only first" >&2
    exit 1
  fi
}

current_mode() {
  if [[ -f "$MARKER" ]]; then
    cat "$MARKER"
  else
    echo "local"
  fi
}

upsert_env_var() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"
  if grep -q "^${key}=" .env; then
    # Avoid sed delimiter issues with URIs containing /
    awk -v k="$key" -v v="$value" '
      BEGIN { done = 0 }
      index($0, k "=") == 1 {
        print k "=" v
        done = 1
        next
      }
      { print }
      END { if (!done) print k "=" v }
    ' .env >"$tmp"
  else
    cat .env >"$tmp"
    printf '%s=%s\n' "$key" "$value" >>"$tmp"
  fi
  mv "$tmp" .env
}

read_env_var() {
  local key="$1"
  local line
  line="$(grep -E "^${key}=" .env | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    echo ""
    return
  fi
  echo "${line#*=}"
}

ensure_ca_cert() {
  mkdir -p "$(dirname "$CA_PATH")"
  if [[ -n "${RING_COCKROACH_CA_CERT:-}" ]]; then
    printf '%s\n' "$RING_COCKROACH_CA_CERT" >"$CA_PATH"
    chmod 600 "$CA_PATH"
    echo "Wrote Cockroach CA cert to ${CA_PATH}"
    return
  fi
  if [[ -f "$CA_PATH" ]]; then
    echo "Using existing Cockroach CA cert at ${CA_PATH}"
    return
  fi
  echo "Missing Cockroach CA cert at ${CA_PATH}" >&2
  echo "Set Cursor secret RING_COCKROACH_CA_CERT (PEM) or place root.crt at that path." >&2
  exit 1
}

resolve_uri() {
  local target="$1"
  local uri=""
  if [[ "$target" == "staging" ]]; then
    uri="${RING_STAGING_COCKROACH_DATABASE_URI:-}"
    if [[ -z "$uri" ]]; then
      echo "Missing secret RING_STAGING_COCKROACH_DATABASE_URI" >&2
      exit 1
    fi
  else
    uri="${RING_PROD_COCKROACH_DATABASE_URI:-}"
    if [[ -z "$uri" ]]; then
      echo "Missing secret RING_PROD_COCKROACH_DATABASE_URI" >&2
      exit 1
    fi
  fi
  # Redact password when echoing host only
  echo "$uri"
}

uri_host_hint() {
  local uri="$1"
  # cockroachdb://user:pass@host:port/db?...
  echo "$uri" | sed -E 's#^[a-z0-9+.-]+://([^/@]+@)?([^:/?]+).*#\2#'
}

confirm_or_die() {
  local target="$1"
  local host="$2"
  local assume_yes="$3"
  cat <<EOF

!!! WARNING: cloud-prod-db mode !!!
  Target:     ${target}
  SQL host:   ${host}
  Frontend:   http://localhost:5173  (Vite → local API → ${target} DB)
  Scheduler:  DISABLED
  Do NOT run migrations against this database from the cloud agent.

EOF
  if [[ "$assume_yes" == "1" ]]; then
    return
  fi
  if [[ ! -t 0 ]]; then
    echo "Non-interactive shell: pass --yes to confirm." >&2
    exit 1
  fi
  read -r -p "Type '${target}' to continue: " answer
  if [[ "$answer" != "$target" ]]; then
    echo "Aborted." >&2
    exit 1
  fi
}

restart_api() {
  local mode="$1"
  if [[ "$mode" == "local" ]]; then
    "${COMPOSE_LOCAL[@]}" up --detach --force-recreate api
  else
    "${COMPOSE_PROD_DB[@]}" up --detach --force-recreate api
  fi
}

wait_for_api() {
  local attempt
  for attempt in $(seq 1 45); do
    if curl -sf "http://localhost:8001/api/v1/openapi.json" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "API did not become ready after switching DB mode" >&2
  return 1
}

cmd_status() {
  require_env_file
  local mode
  mode="$(current_mode)"
  local uri
  uri="$(read_env_var COCKROACH_DATABASE_URI)"
  local host
  host="$(uri_host_hint "$uri")"
  echo "mode:              ${mode}"
  echo "COCKROACH host:    ${host:-<unset>}"
  echo "ENVIRONMENT:       $(read_env_var ENVIRONMENT)"
  echo "DISABLE_SCHEDULER: $(read_env_var DISABLE_SCHEDULER)"
  echo "CA cert:           $([[ -f "$CA_PATH" ]] && echo present || echo missing) (${CA_PATH})"
  echo "prod secret:       $([[ -n "${RING_PROD_COCKROACH_DATABASE_URI:-}" ]] && echo set || echo unset)"
  echo "staging secret:    $([[ -n "${RING_STAGING_COCKROACH_DATABASE_URI:-}" ]] && echo set || echo unset)"
  echo "CA secret:         $([[ -n "${RING_COCKROACH_CA_CERT:-}" ]] && echo set || echo unset)"
}

cmd_enable() {
  local target="prod"
  local assume_yes=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --staging) target="staging" ;;
      --yes|-y) assume_yes=1 ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage >&2
        exit 1
        ;;
    esac
    shift
  done

  require_env_file
  mkdir -p "$STATE_DIR"

  local uri host
  uri="$(resolve_uri "$target")"
  host="$(uri_host_hint "$uri")"
  confirm_or_die "$target" "$host" "$assume_yes"
  ensure_ca_cert

  if [[ ! -f "$ENV_BACKUP" ]]; then
    cp .env "$ENV_BACKUP"
    echo "Backed up .env to ${ENV_BACKUP}"
  fi

  upsert_env_var COCKROACH_DATABASE_URI "$uri"
  upsert_env_var ENVIRONMENT "cloud-${target}-db"
  upsert_env_var DISABLE_SCHEDULER "true"
  # Keep Vite same-origin proxy; do not point the browser at prod nginx.
  upsert_env_var VITE_API_URL ""

  printf '%s\n' "$target" >"$MARKER"

  echo "Recreating API with compose.cloud-prod-db.yml…"
  restart_api "cloud"
  wait_for_api

  cat <<EOF

=== cloud-prod-db enabled (${target}) ===
  App:     http://localhost:5173
  API:     http://localhost:8001/api/v1/docs
  DB host: ${host}
  Login:   use a real ${target} user (seeded test@example.com is local-only)
  Disable: bash dev_util/cloud-prod-db.sh disable
  Health:  bash dev_util/cloud-prod-db.sh health

EOF
}

cmd_disable() {
  require_env_file
  if [[ "$(current_mode)" == "local" && ! -f "$ENV_BACKUP" ]]; then
    echo "Already in local mode."
    return
  fi

  if [[ -f "$ENV_BACKUP" ]]; then
    local local_uri
    local_uri="$(grep -E '^COCKROACH_DATABASE_URI=' "$ENV_BACKUP" | tail -n 1 | cut -d= -f2- || true)"
    if [[ -z "$local_uri" ]]; then
      local_uri="$LOCAL_COCKROACH_URI"
    fi
    upsert_env_var COCKROACH_DATABASE_URI "$local_uri"
    upsert_env_var ENVIRONMENT "local"
    upsert_env_var DISABLE_SCHEDULER "false"
  else
    upsert_env_var COCKROACH_DATABASE_URI "$LOCAL_COCKROACH_URI"
    upsert_env_var ENVIRONMENT "local"
    upsert_env_var DISABLE_SCHEDULER "false"
  fi

  rm -f "$MARKER"
  echo "Recreating API against local Cockroach…"
  restart_api "local"
  wait_for_api
  echo "=== cloud-prod-db disabled (local Cockroach) ==="
}

probe_db_via_api() {
  # SELECT 1 through the running API container (uses the active COCKROACH_DATABASE_URI).
  sudo docker exec ring-api python -c '
from sqlalchemy import text
from ring.sqlalchemy_base import engine
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("ok")
' >/dev/null 2>&1
}

cmd_health() {
  require_env_file
  local mode
  mode="$(current_mode)"
  local errors=0

  if curl -sf "http://localhost:8001/api/v1/openapi.json" >/dev/null; then
    echo "OK  API openapi"
  else
    echo "FAIL API openapi" >&2
    errors=$((errors + 1))
  fi

  if curl -sf "http://localhost:8001/api/v1/docs" >/dev/null; then
    echo "OK  API docs"
  else
    echo "FAIL API docs" >&2
    errors=$((errors + 1))
  fi

  if [[ "$mode" != "local" ]]; then
    if [[ -f "$CA_PATH" ]]; then
      echo "OK  CA cert present"
    else
      echo "FAIL CA cert missing" >&2
      errors=$((errors + 1))
    fi
    local sched
    sched="$(read_env_var DISABLE_SCHEDULER)"
    if [[ "$sched" == "true" || "$sched" == "1" ]]; then
      echo "OK  DISABLE_SCHEDULER=${sched}"
    else
      echo "FAIL DISABLE_SCHEDULER should be true in cloud-prod-db mode (got '${sched}')" >&2
      errors=$((errors + 1))
    fi
    if probe_db_via_api; then
      echo "OK  cloud DB SELECT 1 via API container"
    else
      echo "FAIL cloud DB SELECT 1 via API container" >&2
      errors=$((errors + 1))
    fi
  else
    if sudo docker exec ring-cockroach ./cockroach sql \
      --certs-dir=/root/.cockroach-certs \
      -d ring \
      -e "SELECT 1" >/dev/null 2>&1; then
      echo "OK  local Cockroach"
    else
      echo "FAIL local Cockroach" >&2
      errors=$((errors + 1))
    fi
  fi

  echo "mode: ${mode}"
  if [[ "$errors" -eq 0 ]]; then
    echo "cloud-prod-db health OK"
    exit 0
  fi
  echo "${errors} check(s) failed" >&2
  exit 1
}

main() {
  local cmd="${1:-}"
  if [[ -z "$cmd" ]]; then
    usage >&2
    exit 1
  fi
  shift || true
  case "$cmd" in
    enable) cmd_enable "$@" ;;
    disable) cmd_disable "$@" ;;
    status) cmd_status "$@" ;;
    health) cmd_health "$@" ;;
    -h|--help|help) usage ;;
    *)
      echo "Unknown command: $cmd" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
