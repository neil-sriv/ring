---
name: ring-cloud-dev
description: Bootstrap, health-check, and browser-test Ring in Cursor Cloud Agent VMs. Use when starting compose, Vite, seeding test users, running ring fe regen, or validating the app on the cloud desktop.
---

# Ring Cloud Dev

Playbook for agents working in the **Cursor Cloud Agent VM** on this repo.

## One-command bootstrap

The environment `start` hook runs backend bootstrap; the `vite` terminal starts the
frontend. To run manually:

```bash
bash .cursor/cloud-start.sh --bootstrap-only   # Docker, DB, seed user
bash .cursor/cloud-start.sh --vite-only        # Vite on :5173
# or both:
bash .cursor/cloud-start.sh
```

## Ready state

After bootstrap, grep for `=== Ring cloud ready ===` or run:

```bash
bash dev_util/cloud-health.sh
```

| Service | URL |
|---------|-----|
| App (Vite) | http://localhost:5173 |
| API (direct) | http://localhost:8001/api/v1/docs |
| API (nginx) | https://localhost/api/v1/docs |

## Test login

Seeded on bootstrap (idempotent):

- Email: `test@example.com`
- Password: `testpassword123`

Re-seed manually: `bash dev_util/cloud-seed.sh`

## API client from browser

Vite proxies `/api/v1` → `http://localhost:8001`. Cloud `.env` uses **empty**
`VITE_API_URL` (see `.env.cloud.example`). Do **not** set
`VITE_API_URL=https://localhost` with HTTP Vite — browsers block mixed content
and login fails silently.

Local OrbStack dev may still use `VITE_API_URL=https://localhost` when hitting
nginx TLS directly (no Vite proxy).

## `ring fe regen`

Requires the API container on `:8001`:

```bash
source .venv/bin/activate
ring fe regen
```

## Raw compose (debugging only)

```bash
source .venv/bin/activate
sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev up --build --detach
sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev \
  exec -w /src/ring api alembic upgrade head
```

Vector index (handled by `cloud-start.sh`, run manually if migrations fail):

```bash
sudo docker exec ring-cockroach ./cockroach sql \
  --certs-dir=/root/.cockroach-certs -d ring \
  -e "SET CLUSTER SETTING feature.vector_index.enabled = true;"
```

## `.env`

Gitignored. Created from `.env.cloud.example` on first bootstrap. SSL:
`bash dev_util/ssl.sh`; `chmod 600 certs/node.key`.

## Browser testing

1. Open http://localhost:5173/login
2. Log in with the test account above
3. Expect redirect to the dashboard with sidebar navigation

Nginx at `https://localhost/` serves `react/dist` only (404 for SPA routes
unless built). Use Vite for frontend testing.

## Notebook / WebSocket note

Collaborative notebook WebSockets may still use `VITE_API_URL` for `wss://`
URLs. If notebook sync fails in cloud, set `VITE_API_URL=http://localhost:8001`
for those code paths or test notebook features via nginx production build.
