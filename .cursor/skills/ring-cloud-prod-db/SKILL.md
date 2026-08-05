---
name: ring-cloud-prod-db
description: Point a Cursor Cloud Agent local Vite + API stack at CockroachDB Cloud (prod or staging) so frontend work can use real data. Use when working in the "Ring client only" environment, connecting the cloud agent frontend to the prod database, or enabling cloud-prod-db mode.
---

# Ring Cloud → Prod / Staging DB

## Which Cloud Agent environment?

| Environment | Purpose |
|-------------|---------|
| **Ring full stack** | Default. Local Docker Cockroach + API + Vite. Repo file: [`.cursor/environment.json`](../../../.cursor/environment.json). |
| **Ring client only** | FE-focused work against **prod** (or staging) data. Create this as a **separate saved environment in the Cursor dashboard** — do **not** add a second `environment.json` to the repo. |

Cursor resolves config in order: repo `.cursor/environment.json` → personal saved env → team saved env. Keep the committed file as **Ring full stack**. Configure **Ring client only** only in the [Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents#environments) (same Dockerfile/repo, different `install`/`start`/secrets). Attach the Cockroach secrets to **Ring client only**, not to full stack, so ordinary agents do not get prod DB credentials.

Suggested **Ring client only** runtime shape (dashboard fields; tune as needed):

- **install** — same as full stack is fine (`uv sync`, `pnpm install`, SSL), or skip unused bits if you want a thinner Build.
- **start** — bring up API (and Docker if needed), then `ring cloud prod-db enable --yes`, then Vite. Example:

```bash
sudo service docker start
bash .cursor/cloud-start.sh --bootstrap-only
ring cloud prod-db enable --yes
```

- **terminals** — Vite: `bash .cursor/cloud-start.sh --vite-only` (or `ring fe dev`)

You still need a **local API** for this workflow. “Client only” means no reliance on local Cockroach data / FE-against-prod — not “Vite with no backend.” Keep `VITE_API_URL` empty so Vite proxies `/api/v1` → `:8001`.

## Topology

```
Browser / Vite (:5173)
  → same-origin /api/v1 (Vite proxy)
  → local ring-api (:8001)
  → CockroachDB Cloud (prod or staging)
```

Do **not** point the browser at `https://ring.neilsriv.tech` from the cloud desktop (mixed-origin / CORS pain).

## `ring cloud prod-db` — any environment?

Yes. The CLI is part of the shared `ring` toolchain and works in **any** Cloud Agent (or laptop) that has:

1. `.env` from bootstrap
2. Docker + `ring-api` running
3. The secrets below injected

Prefer running it from **Ring client only**. On **Ring full stack**, only enable when you intentionally want cloud data; disable before finishing so the next run is local again.

## Prerequisites

### Secrets (on **Ring client only**)

| Secret | Required | Purpose |
|--------|----------|---------|
| `RING_PROD_COCKROACH_DATABASE_URI` | for prod | Full `cockroachdb://…` URI for cluster `ring-db` |
| `RING_STAGING_COCKROACH_DATABASE_URI` | for staging | Full URI for `ring-db-staging` |
| `RING_COCKROACH_CA_CERT` | yes | PEM body of the Cockroach Cloud CA (`root.crt`) |

Copy the URI from the server `.env` (`COCKROACH_DATABASE_URI`) or the Cockroach Cloud console. Prefer a **read-only SQL user** when the task is frontend-only. Use **Runtime Secret** so URIs stay redacted in transcripts.

The CA PEM is the same file prod mounts at `$HOME/.postgresql/root.crt`
(see [compose.prod.yml](../../../compose.prod.yml)).

### Network

If the environment uses **Allow all network access**, no extra egress config is required. If egress is allowlisted, add the SQL host (e.g. `gcp-us-east1.cockroachlabs.cloud` or the host from `ring cloud prod-db status`).

### Local stack

On **Ring full stack** (or before first `enable` on client only):

```bash
bash .cursor/cloud-start.sh --bootstrap-only
bash .cursor/cloud-start.sh --vite-only   # or the vite terminal
```

`ring` is on `PATH` after `uv sync` (Cloud Agent install already runs it).

## Enable / disable

**Ring client only** normally targets **prod**:

```bash
ring cloud prod-db status
ring cloud prod-db enable --yes
ring cloud prod-db health
```

Staging (any env that has the staging secret):

```bash
ring cloud prod-db enable --staging --yes
```

Restore local Docker Cockroach:

```bash
ring cloud prod-db disable
```

What `enable` does:

1. Backs up `.env` under `.ring-cloud-prod-db/`
2. Writes CA cert to `~/.postgresql/root.crt` from `RING_COCKROACH_CA_CERT`
3. Sets `COCKROACH_DATABASE_URI`, `ENVIRONMENT=cloud-{prod|staging}-db`,
   `DISABLE_SCHEDULER=true`, empty `VITE_API_URL`
4. Recreates `api` with [compose.cloud-prod-db.yml](../../../compose.cloud-prod-db.yml)
   (mounts CA + forces scheduler off)

Implementation: [dev_util/cloud.py](../../../dev_util/cloud.py).

## Frontend login

The seeded `test@example.com` user exists only on local Cockroach. Against
cloud DB, log in with a real prod/staging account. JWT is minted by the
**local** API; password hashes come from the cloud DB.

## Hard rules (agents)

- **Never** run `ring db upgrade`, `ring db generate`, or alembic against the
  cloud URI from this mode.
- **Never** commit `.env`, `.ring-cloud-prod-db/`, or `~/.postgresql/root.crt`.
- On prod, avoid destructive writes; treat data as live.
- Leave APScheduler disabled (`DISABLE_SCHEDULER=true`).
- On **Ring full stack**, run `ring cloud prod-db disable` when finished.

## Browser check

1. Open http://localhost:5173/login
2. Sign in with a cloud-DB user
3. Confirm groups/letters match prod/staging, not the empty local seed

## Related

- Full-stack bootstrap: [ring-cloud-dev](../ring-cloud-dev/SKILL.md)
- Prod topology: [docs/infrastructure.md](../../../docs/infrastructure.md)
