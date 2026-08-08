#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE=(sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev)
MODE="${1:-all}"

ensure_network() {
  if ! sudo docker network inspect ring-network >/dev/null 2>&1; then
    sudo docker network create ring-network
  fi
}

ensure_ssl() {
  if [[ ! -f localhost.crt || ! -f localhost.key ]]; then
    bash dev_util/ssl.sh
  fi
}

ensure_env() {
  if [[ -f .env ]]; then
    return
  fi

  if [[ -f .env.cloud.example ]]; then
    cp .env.cloud.example .env
  else
    cat > .env <<'EOF'
ENVIRONMENT=local
API_PORT=8001
SQLALCHEMY_DATABASE_URI=postgresql://ring-postgres:ring-postgres@db:5432/ring
COCKROACH_DATABASE_URI=cockroachdb://ringcockroach:ringcockroach@cockroach:26257/ring?sslmode=require
JWT_SIGNING_ALGORITHM=HS256
VITE_API_URL=
BACKEND_CORS_ORIGINS="https://localhost:5173 http://localhost:5173"
SW_DEV=false
VITE_MAINTENANCE_MODE=false
EOF
  fi

  {
    echo "JWT_SIGNING_KEY=$(openssl rand -hex 32)"
    echo "LLM_SERVICE_API_KEY=$(openssl rand -hex 32)"
    echo "VAPID_PRIVATE_KEY=$(openssl rand -hex 32)"
  } >> .env
}

wait_for_cockroach() {
  local attempt
  for attempt in $(seq 1 60); do
    if sudo docker exec ring-cockroach ./cockroach sql \
      --certs-dir=/root/.cockroach-certs \
      -d ring \
      -e "SELECT 1" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "CockroachDB did not become ready in time" >&2
  return 1
}

wait_for_api() {
  local attempt
  for attempt in $(seq 1 60); do
    if curl -sf "http://localhost:8001/api/v1/openapi.json" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "API did not become ready in time" >&2
  return 1
}

enable_vector_index() {
  sudo docker exec ring-cockroach ./cockroach sql \
    --certs-dir=/root/.cockroach-certs \
    -d ring \
    -e "SET CLUSTER SETTING feature.vector_index.enabled = true;" \
    || true
}

seed_test_user() {
  bash dev_util/cloud-seed.sh
}

print_ready_banner() {
  local vite_note="${1:-}"
  cat <<EOF

=== Ring cloud ready ===
  App:    http://localhost:5173
  API:    http://localhost:8001/api/v1/docs
  Nginx:  https://localhost/api/v1/docs
  Login:  test@example.com / testpassword123
  Health: bash dev_util/cloud-health.sh
${vite_note}
EOF
}

run_bootstrap() {
  ensure_network
  ensure_ssl
  if [[ -f certs/node.key ]]; then
    chmod 600 certs/node.key
  fi
  ensure_env

  "${COMPOSE[@]}" up --build --detach

  wait_for_cockroach
  enable_vector_index

  "${COMPOSE[@]}" exec -T -w /src/ring api alembic upgrade head

  wait_for_api
  seed_test_user

  print_ready_banner "  Vite:   starts in the vite terminal (pnpm run dev)"
}

run_vite() {
  cd "$ROOT/react"
  # Force same-origin /api/v1 via the Vite proxy. Cursor Cloud secrets (and other
  # shell env) often inject VITE_API_URL=https://localhost for nginx TLS; Vite
  # prefers process env over .env, which breaks HTTP Vite with CERT errors /
  # mixed-content. Always clear it for the cloud Vite path.
  export VITE_API_URL=""
  # Service worker registration in HTTP cloud Vite is unused noise.
  # Force false: Cursor secrets often inject SW_DEV=true, and
  # `${SW_DEV:-false}` would keep that injected value.
  export SW_DEV=false
  exec pnpm run dev -- --host 0.0.0.0
}

case "$MODE" in
  --bootstrap-only)
    run_bootstrap
    ;;
  --vite-only)
    run_vite
    ;;
  all|"")
    run_bootstrap
    run_vite
    ;;
  *)
    echo "Usage: $0 [--bootstrap-only | --vite-only | all]" >&2
    exit 1
    ;;
esac
