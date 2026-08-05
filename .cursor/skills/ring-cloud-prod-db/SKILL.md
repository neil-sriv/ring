---
name: ring-cloud-prod-db
description: Point a Cursor Cloud Agent local Vite + API stack at the live CockroachDB Cloud database so frontend work can use real data. Use when working in the "Ring client only" environment, connecting the cloud agent frontend to the prod database, or enabling cloud-prod-db mode.
---

# Ring Cloud → Production DB

## There is no staging

Ring has **one live Cockroach Cloud cluster**. Despite its name,
**`ring-db-staging` is the cluster `ring.neilsriv.tech` serves from**; the
cluster named `ring-db` is stale and unused.

Every connection made through this skill touches **live user data**. There is no
safe copy to rehearse against — treat all writes as production writes.

## Which Cloud Agent environment?

| Environment | Purpose |
|-------------|---------|
| **Ring full stack** | Default. Local Docker Cockroach + API + Vite. Repo file: [`.cursor/environment.json`](../../../.cursor/environment.json). |
| **Ring client only** | FE work against **live prod** data. Create this as a **separate saved environment in the Cursor dashboard** — do **not** add a second `environment.json` to the repo. |

Cursor resolves config in order: repo `.cursor/environment.json` → personal
saved env → team saved env. Keep the committed file as **Ring full stack**.
Configure **Ring client only** only in the
[Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents#environments)
(same Dockerfile/repo, different `install`/`start`/secrets). Attach the
Cockroach secrets to **Ring client only**, not to full stack, so ordinary agents
do not hold live DB credentials.

Suggested **Ring client only** runtime shape (dashboard fields; tune as needed):

- **install** — same as full stack is fine (`uv sync`, `pnpm install`, SSL), or
  skip unused bits for a thinner Build.
- **start** — bring up the API, then enable prod DB, then Vite:

```bash
sudo service docker start
bash .cursor/cloud-start.sh --bootstrap-only
ring cloud prod-db enable --yes
```

- **terminals** — Vite: `bash .cursor/cloud-start.sh --vite-only` (or `ring fe dev`)

You still need a **local API**. "Client only" means the frontend runs against
prod data rather than local seed data — not "Vite with no backend." Keep
`VITE_API_URL` empty so Vite proxies `/api/v1` → `:8001`.

## Topology

```
Browser / Vite (:5173)
  → same-origin /api/v1 (Vite proxy)
  → local ring-api (:8001)
  → CockroachDB Cloud (live)
```

Do **not** point the browser at `https://ring.neilsriv.tech` from the cloud
desktop (mixed-origin / CORS pain).

## `ring cloud prod-db` — any environment?

Yes. The CLI ships with the shared `ring` toolchain and works in **any** Cloud
Agent (or laptop) that has:

1. `.env` from bootstrap
2. Docker + `ring-api` running
3. The secrets below injected

Access is gated by **which environment holds the secrets**, not by the CLI.
Prefer running it from **Ring client only**. On **Ring full stack**, only enable
when you intentionally want live data, and disable before finishing.

## Prerequisites

### Secrets (on **Ring client only**)

| Secret | Purpose |
|--------|---------|
| `RING_COCKROACH_DATABASE_URI` | Full `cockroachdb://…` URI for the live cluster (`ring-db-staging`) |
| `RING_COCKROACH_CA_CERT` | PEM body of the Cockroach Cloud CA (`root.crt`) |

Copy the URI from the server `.env` (`COCKROACH_DATABASE_URI`) or the Cockroach
Cloud console. Use a **read-only SQL user** whenever the task is frontend-only —
that is the only real safeguard available, since there is no staging copy. Set
both as **Runtime Secret** so values stay redacted in transcripts.

The CA PEM is the same file prod mounts at `$HOME/.postgresql/root.crt`
(see [compose.prod.yml](../../../compose.prod.yml)).

### Network

With **Allow all network access**, no extra egress config is required. Under
allowlist mode, add the SQL host (e.g. `gcp-us-east1.cockroachlabs.cloud`, or
the host printed by `ring cloud prod-db status`).

### Local stack

```bash
bash .cursor/cloud-start.sh --bootstrap-only
bash .cursor/cloud-start.sh --vite-only   # or the vite terminal
```

`ring` is on `PATH` after `uv sync` (the Cloud Agent install already runs it).

## Enable / disable

```bash
ring cloud prod-db status
ring cloud prod-db enable --yes
ring cloud prod-db health
```

`enable` prints a live-data warning and requires typing `prod` unless `--yes` is
passed. Restore local Docker Cockroach when finished:

```bash
ring cloud prod-db disable
```

What `enable` does:

1. Backs up `.env` under `.ring-cloud-prod-db/`
2. Writes CA cert to `~/.postgresql/root.crt` from `RING_COCKROACH_CA_CERT`
3. Sets `COCKROACH_DATABASE_URI`, `ENVIRONMENT=cloud-prod-db`,
   `DISABLE_SCHEDULER=true`, empty `VITE_API_URL`
4. Recreates `api` with [compose.cloud-prod-db.yml](../../../compose.cloud-prod-db.yml)
   (mounts CA + forces scheduler off)

Implementation: [dev_util/cloud.py](../../../dev_util/cloud.py).

## Frontend login

The seeded `test@example.com` user exists only on local Cockroach. Against the
cloud DB, log in with a real account. JWT is minted by the **local** API;
password hashes come from the cloud DB.

## Hard rules (agents)

- **Never** run `ring db upgrade`, `ring db generate`, or alembic against the
  cloud URI from this mode.
- **Never** commit `.env`, `.ring-cloud-prod-db/`, or `~/.postgresql/root.crt`.
- Avoid destructive writes entirely; this is live user data with no staging
  fallback. Prefer a read-only SQL user.
- Leave APScheduler disabled (`DISABLE_SCHEDULER=true`).
- On **Ring full stack**, run `ring cloud prod-db disable` when finished.

## Browser check

1. Open http://localhost:5173/login
2. Sign in with a real account
3. Confirm groups/letters match prod, not the empty local seed

## Related

- Full-stack bootstrap: [ring-cloud-dev](../ring-cloud-dev/SKILL.md)
- Prod topology: [docs/infrastructure.md](../../../docs/infrastructure.md)
