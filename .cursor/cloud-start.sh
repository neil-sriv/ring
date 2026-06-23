#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE=(sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev)

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

  cat > .env <<'EOF'
ENVIRONMENT=local
API_PORT=8001
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
SQLALCHEMY_DATABASE_URI=postgresql://ring-postgres:ring-postgres@db:5432/ring
COCKROACH_DATABASE_URI=cockroachdb://ringcockroach:ringcockroach@cockroach:26257/ring?sslmode=require
JWT_SIGNING_ALGORITHM=HS256
VITE_API_URL=https://localhost
BACKEND_CORS_ORIGINS="https://localhost:5173 http://localhost:5173"
SW_DEV=true
VITE_MAINTENANCE_MODE=false
EOF

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

enable_vector_index() {
  sudo docker exec ring-cockroach ./cockroach sql \
    --certs-dir=/root/.cockroach-certs \
    -d ring \
    -e "SET CLUSTER SETTING feature.vector_index.enabled = true;" \
    || true
}

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

cd react
exec pnpm run dev -- --host 0.0.0.0
