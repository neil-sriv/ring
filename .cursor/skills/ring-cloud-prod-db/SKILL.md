---
name: ring-cloud-prod-db
description: Point a Cursor Cloud Agent local Vite + API stack at CockroachDB Cloud (prod or staging) so frontend work can use real data. Use when the user asks to connect the cloud agent frontend to the prod database, run against staging/prod data, or enable cloud-prod-db mode.
---

# Ring Cloud → Prod / Staging DB

Use this when a **Cloud Agent local frontend** (Vite on `:5173`) should talk to
**real CockroachDB Cloud data** instead of the local Docker Cockroach.

Topology while enabled:

```
Browser / Vite (:5173)
  → same-origin /api/v1 (Vite proxy)
  → local ring-api (:8001)
  → CockroachDB Cloud (prod or staging)
```

Keep `VITE_API_URL` empty. Do **not** point the browser at
`https://ring.neilsriv.tech` — that bypasses the local API and hits mixed-origin
/ CORS issues from the cloud desktop.

## Prerequisites

### 1. Cursor secrets

Add these on the Cloud Agent environment (dashboard secrets), then restart the
agent so they are injected:

| Secret | Required | Purpose |
|--------|----------|---------|
| `RING_PROD_COCKROACH_DATABASE_URI` | for prod | Full `cockroachdb://…` URI for cluster `ring-db` |
| `RING_STAGING_COCKROACH_DATABASE_URI` | for staging | Full URI for `ring-db-staging` |
| `RING_COCKROACH_CA_CERT` | yes | PEM body of the Cockroach Cloud CA (`root.crt`) |

Copy the URI from the server `.env` (`COCKROACH_DATABASE_URI`) or the Cockroach
Cloud console. Prefer a **read-only SQL user** when the task is frontend-only.

The CA PEM is the same file prod mounts at `$HOME/.postgresql/root.crt`
(see [compose.prod.yml](../../../compose.prod.yml)).

### 2. Egress allowlist

Cloud Agent egress is restricted. Allow the SQL hostname from the URI (and/or
the regional parent), for example:

- `gcp-us-east1.cockroachlabs.cloud` (Ring’s Cockroach Cloud region)
- or the exact host printed by `bash dev_util/cloud-prod-db.sh status`

If enable fails with connection timeouts / TLS dial errors, request that domain
via `cursor-cloud/request-environment-setup-actions`.

### 3. Local stack already up

```bash
bash .cursor/cloud-start.sh --bootstrap-only
bash .cursor/cloud-start.sh --vite-only   # or use the vite terminal
```

## Enable / disable

Prefer **staging** unless the user explicitly needs prod:

```bash
bash dev_util/cloud-prod-db.sh status
bash dev_util/cloud-prod-db.sh enable --staging --yes
# or prod:
bash dev_util/cloud-prod-db.sh enable --yes

bash dev_util/cloud-prod-db.sh health
```

Restore local Docker Cockroach when done:

```bash
bash dev_util/cloud-prod-db.sh disable
```

What `enable` does:

1. Backs up `.env` under `.ring-cloud-prod-db/`
2. Writes CA cert to `~/.postgresql/root.crt` from `RING_COCKROACH_CA_CERT`
3. Sets `COCKROACH_DATABASE_URI`, `ENVIRONMENT=cloud-{prod|staging}-db`,
   `DISABLE_SCHEDULER=true`, empty `VITE_API_URL`
4. Recreates `api` with [compose.cloud-prod-db.yml](../../../compose.cloud-prod-db.yml)
   (mounts CA + forces scheduler off)

## Frontend login

The seeded `test@example.com` user exists only on local Cockroach. Against
cloud DB, log in with a real prod/staging account (or create one via the API if
appropriate). JWT is still minted by the **local** API (`JWT_SIGNING_KEY` in
cloud `.env`) — that is fine; password hashes come from the cloud DB.

## Hard rules (agents)

- **Never** run `ring db upgrade`, `ring db generate`, or alembic against the
  cloud URI from this mode.
- **Never** commit `.env`, `.ring-cloud-prod-db/`, or `~/.postgresql/root.crt`.
- Prefer staging. On prod, avoid destructive writes; treat data as live.
- Leave APScheduler disabled (`DISABLE_SCHEDULER=true`) — the local API must not
  fire letter/reminder/email jobs against cloud data.
- When finished testing, run `disable` so the next agent boots on local DB.

## Browser check

1. Open http://localhost:5173/login
2. Sign in with a cloud-DB user
3. Confirm groups/letters match prod/staging, not the empty local seed

## Related

- Default cloud bootstrap: [ring-cloud-dev](../ring-cloud-dev/SKILL.md)
- Prod topology: [docs/infrastructure.md](../../../docs/infrastructure.md)
