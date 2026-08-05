# AGENTS.md

Project guide for AI coding agents working on **Ring**, a collaborative
letter/newsletter platform (LetterLoop-style). Human-oriented setup lives in
[README.md](README.md); this file focuses on what agents need to be productive.

---

## Overview

Ring lets a group of people answer prompts on a cadence, then publishes the
collected responses as a "letter." It is built as a FastAPI backend with a
React/Vite frontend, fronted by Nginx, backed by CockroachDB, with an optional
LLM microservice.

## Architecture

| Component       | Tech                                         | Default port  |
|-----------------|----------------------------------------------|---------------|
| Backend API     | FastAPI + SQLAlchemy 2 + Alembic             | 8001 (Docker) |
| Frontend        | React + Vite + Tailwind v4 + Radix/shadcn + TanStack | 5173 (Vite dev)|
| Reverse proxy   | Nginx (TLS, `/api/v1/`)                      | 443/80        |
| Database        | CockroachDB (Postgres-compatible)            | 26257         |
| LLM (optional)  | Local microservice in [llm/](llm/)           | varies        |

The frontend talks to the backend via the Nginx proxy at
`https://localhost/api/v1/`. Direct access to the API container on `:8001` is
used only by tooling (e.g. OpenAPI spec fetching).

### Infrastructure & external services (production)

Local dev uses Docker Compose with a local CockroachDB container. **Production**
is a single EC2 host running the same Compose stack, plus managed services below.
Full topology, request flows, and deploy steps:
[docs/infrastructure.md](docs/infrastructure.md).

| Service | Identifier / endpoint | Code / config |
|---------|----------------------|---------------|
| Compute | EC2 + Docker Compose (`ring.neilsriv.tech`) | [compose.prod.yml](compose.prod.yml), [prod.nginx.conf](prod.nginx.conf) |
| Database | CockroachDB Cloud `ring-db` (not RDS) | `COCKROACH_DATABASE_URI` in server `.env` |
| S3 uploads | Bucket `rings3files` (`us-east-1`) | [ring/fastapp/config.py](ring/fastapp/config.py) `BUCKET_NAME`; upload in [ring/letters/crud/response.py](ring/letters/crud/response.py) |
| CDN | `du32exnxihxuf.cloudfront.net` | [ring/s3/models/s3_model.py](ring/s3/models/s3_model.py) `qualified_s3_url` |
| Email (SES) | `us-east-1`, sender `ring@neilsriv.tech` | [ring/email_util.py](ring/email_util.py) |
| Container registry | ECR Public `public.ecr.aws/z2k1e8p1/` | [dev_util/docker.py](dev_util/docker.py), [dev_util/prod.sh](dev_util/prod.sh) |

Do not assume ECS, RDS, Route 53, Redis/Celery, Lambda, or Bedrock — none are
in the current prod path. Embeddings go through the optional `ring-llm`
microservice; background work uses in-process APScheduler, not Celery.

## Codebase map

### Backend (`ring/`)

Domain packages each follow the same internal shape:

```
ring/<domain>/
  api/        # FastAPI routers
  crud/       # SQLAlchemy queries / mutations
  models/     # SQLAlchemy ORM models
  schemas/    # Pydantic request/response schemas
```

Important domains and shared modules:

- `ring/parties/` — users, groups, invites, group key/values
- `ring/letters/` — letters, questions, responses, default questions
- `ring/tasks/` — scheduling
- `ring/notifications/` — push/email subscriptions
- `ring/notebook/` — collaborative notebook (Automerge / Y.js)
- `ring/search/` — search endpoints (CockroachDB vector index)
- `ring/auth/` — authentication routes
- `ring/authz/` — Casbin-based authorization ([authz.py](ring/authz/authz.py))
- `ring/api_identifier/` — `APIIdentified` mixin + `APIPrefix` enum
- `ring/fastapp/` — app factory; routers are wired in
  [ring/fastapp/routes.py](ring/fastapp/routes.py)
- `ring/security.py` — password hashing, JWT access tokens
- `ring/alembic/` — migrations

### Frontend (`react/src/`)

- `client/` — generated `@hey-api` SDK + TanStack Query hooks
  (`sdk.gen.ts`, `types.gen.ts`, `client.gen.ts`, `@tanstack/`)
- `components/` — feature components; `components/ui/` holds shadcn primitives
- `routes/` — TanStack Router file-based routes; `routeTree.gen.ts` is generated
- `hooks/`, `lib/`, `util/` — shared frontend code

## Key conventions

- **API identifiers.** Models that are addressable through the API extend
  `APIIdentified` (see
  [ring/api_identifier/api_identified_model.py](ring/api_identifier/api_identified_model.py)),
  declare an `API_ID_PREFIX` from `APIPrefix`, and register with
  `@register_api_class(APIPrefix.X)`. IDs look like `grp_<uuid>`, `lttr_<uuid>`,
  etc. Use `bulk_get_models` / `get_model` to look them up by prefix.
- **Authz.** Use `ring/authz/authz.py` helpers (`load_and_check`,
  `bulk_load_and_check`, `check`, `filter_to_authorized`,
  `bulk_can_or_inaccessible`) for permission checks. Follow patterns in sibling
  routes inside the same domain rather than inventing new flows.
- **Routers.** All routers are registered in
  [ring/fastapp/routes.py](ring/fastapp/routes.py); add new ones there.
- **Generated frontend client.** The frontend never hand-writes API calls.
  After backend changes that touch the OpenAPI surface, regenerate with
  `ring fe regen` and use the generated TanStack Query hooks under
  `react/src/client/`.
- **Generic attachable entities.** Secondary entities that can attach to many
  parent types should use a **weak reference** — store the parent's
  `api_identifier` in a `target_api_id` column, look it up with
  `bulk_get_models`, and skip polymorphic FKs. Prefer **hard deletes** over
  soft-delete columns unless a specific feature requires undo. Pick a new
  3–6 character prefix in `APIPrefix` when adding such an entity.

## Dev workflow

The `ring` CLI (installed via `uv sync`) wraps Docker Compose and common
commands. See [README.md](README.md) for the full list and one-time setup.

Common loop:

```bash
source .venv/bin/activate
ring compose up           # CockroachDB + API + Nginx
ring db upgrade           # apply migrations
ring fe dev               # Vite at https://localhost:5173
```

When backend API shape changes:

```bash
ring db generate "<message>"  # create alembic revision (autogenerate)
ring db upgrade               # apply
ring fe regen                 # refresh react/src/client/ from OpenAPI
```

### Cursor Cloud Agent VM

Use the [**ring-cloud-dev** skill](.cursor/skills/ring-cloud-dev/SKILL.md).
Bootstrap is automated via [`.cursor/cloud-start.sh`](.cursor/cloud-start.sh)
and [`.cursor/environment.json`](.cursor/environment.json); copy
[`.env.cloud.example`](.env.cloud.example) for cloud `.env` defaults.

```bash
bash .cursor/cloud-start.sh --bootstrap-only
bash dev_util/cloud-health.sh
```

Do not hand-roll compose unless debugging — the start script handles network,
SSL, vector index, migrations, and a test user seed.

To point the **local Vite frontend + local API** at CockroachDB Cloud (prod or
staging) instead of Docker Cockroach, use
[**ring-cloud-prod-db**](.cursor/skills/ring-cloud-prod-db/SKILL.md):

```bash
ring cloud prod-db enable --staging --yes   # or: ring cloud prod-db enable --yes
ring cloud prod-db disable                  # back to local
```

Requires Cursor secrets `RING_PROD_COCKROACH_DATABASE_URI` /
`RING_STAGING_COCKROACH_DATABASE_URI` and `RING_COCKROACH_CA_CERT`, plus egress
for Cockroach Cloud SQL hosts. Never run migrations against the cloud URI from
this mode.

## Quality gates

| Check                | Command                                                        |
|----------------------|----------------------------------------------------------------|
| Python lint/format   | `ring check lint` (`uv run ruff format --diff && ruff check`)  |
| Frontend lint        | `cd react && pnpm run lint` (Biome; ~21 pre-existing warnings) |
| TypeScript           | `cd react && npx tsc --noEmit`                                 |
| Frontend build       | `cd react && pnpm run build`                                   |
| Backend tests        | `ring test run` (Compose `compose.test.yml`, profile `test`)   |

Backend tests run inside a dedicated `ring-test-runner` container against a
separate CockroachDB instance on port 8008.

## Design preferences

- **Split big changes into PRs.** Land backend (models, migrations, API,
  tests, OpenAPI) first; follow with `ring fe regen` + UI in a second PR. Each
  PR should pass `ring check lint` and the relevant tests on its own.
- **Prefer existing timeout mechanisms.** For operational resilience (e.g.
  long-running image uploads), use Nginx proxy timeouts and the
  botocore/boto3 / FastAPI built-in timeouts rather than rolling custom
  middleware.
- **Don't assume features that aren't there.** Today the JWT access token is
  long-lived (~1 week, see [ring/security.py](ring/security.py)) and there is
  no refresh-token flow. Don't invent one as a "preference" — implement it
  explicitly if asked, and document the change at that point.

## Agent resources

- [.cursor/rules/](.cursor/rules/) — file-scoped style rules (`python.mdc`,
  `react.mdc`).
- [.cursor/skills/](.cursor/skills/) — repeatable task playbooks:
  - `ring-add-backend-resource/` — new domain endpoint/model/CRUD
  - `ring-regen-frontend-client/` — refresh `react/src/client/` after API
    changes
  - `ring-authz-checklist/` — permission-check patterns for new routes
  - `ring-split-pr/` — splitting backend + frontend work into separate PRs
  - `ring-db-migration/` — generate/modify Alembic migrations the correct way
  - `ring-cloud-dev/` — Cursor Cloud VM bootstrap, health checks, browser testing
  - `ring-cloud-prod-db/` — point cloud Vite/API at CockroachDB Cloud (prod/staging)
  - `ring-deploy-prod/` — build + push prod images to public ECR (`ring deploy prod`)
