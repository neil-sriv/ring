# ring

A collaborative letter/newsletter platform (LetterLoop-style). A group answers prompts on a cadence, and Ring publishes the responses as a letter. Setup is in [README.md](README.md).

Merges to `dev` deploy to production on their own. Treat every backend-touching PR as a deploy. Identifiers and agent deploy rules: [docs/deploy.md](docs/deploy.md). Topology: [docs/infrastructure.md](docs/infrastructure.md). Deploy runbook: [docs/continuous-deploy.md](docs/continuous-deploy.md).

## Stack

| Part | Tech | Default |
| --- | --- | --- |
| Backend `ring/` | FastAPI, SQLAlchemy 2, Alembic | 8001 (Docker). Direct `:8001` is tooling only, such as the OpenAPI fetch. |
| Frontend `react/` | React, Vite, Tailwind v4, Radix and shadcn, TanStack | `http://localhost:5173` |
| Proxy | Nginx, TLS, API at `/api/v1/` | 443 and 80. The app API base is `https://localhost/api/v1/`. |
| Database | CockroachDB, Postgres-compatible | 26257 |
| LLM `llm/` | Optional microservice | 8006 (`LLM_PORT`) |

Do not assume ECS, RDS, Route 53, Redis or Celery, Lambda, or Bedrock. Embeddings go through the optional `ring-llm` microservice. Background work is in-process APScheduler.

`ring fe dev` proxies `/api/v1` to port 8001. Local env sets `BACKEND_CORS_ORIGINS` to `https://localhost:5173` and `http://localhost:5173`.

## Commands

The `ring` CLI comes from `uv sync --group dev --group ai`. Activate with `source .venv/bin/activate`.

```bash
ring compose up        # CockroachDB, API, Nginx
ring db upgrade        # apply migrations
ring fe dev            # Vite at http://localhost:5173
ring db generate "<message>"   # new Alembic revision, pins ring/alembic/head
ring fe regen          # refresh react/src/client/ from OpenAPI
ring gen imports       # after adding a model, job, search function, API class, or test factory
ring deploy status     # what frontend and API are running
```

Cloud agent VM: use [`.cursor/skills/ring-cloud-dev/SKILL.md`](.cursor/skills/ring-cloud-dev/SKILL.md). Bootstrap is [`.cursor/cloud-start.sh`](.cursor/cloud-start.sh) and [`.cursor/environment.json`](.cursor/environment.json). Copy [`.env.cloud.example`](.env.cloud.example) for cloud `.env` defaults.

```bash
bash .cursor/cloud-start.sh --bootstrap-only
bash dev_util/cloud-health.sh
```

Do not hand-roll compose unless debugging. The start script handles network, SSL, the vector index, migrations, and a test user seed.

To point local Vite and the local API at CockroachDB Cloud, use [`.cursor/skills/ring-cloud-prod-db/SKILL.md`](.cursor/skills/ring-cloud-prod-db/SKILL.md):

```bash
ring cloud prod-db enable --staging --yes   # or: ring cloud prod-db enable --yes
ring cloud prod-db disable                  # back to local
```

That mode needs Cursor secrets `RING_PROD_COCKROACH_DATABASE_URI`, `RING_STAGING_COCKROACH_DATABASE_URI`, and `RING_COCKROACH_CA_CERT`, plus egress to the Cockroach Cloud SQL host.

## Quality gates

| Check | Command |
| --- | --- |
| Python lint | `ring check lint` (`ruff format --diff`, `ruff check`, `ring gen imports --check`, `ring gen genesis-idp --check`) |
| Frontend lint | `cd react && pnpm run lint`. It runs Biome with `--apply-unsafe` and rewrites files, so read the diff. |
| Types and build | `cd react && pnpm run build` (`tsc && vite build`) |
| Backend tests | `ring test run` |
| Migrations | `ring db check-alembic-head`, `ring db check-migrations`, `ring db check-schema-drift` |

CI runs lint and tests on every PR and migration checks in [`.github/workflows/check_migrations.yml`](.github/workflows/check_migrations.yml). Backend tests run in the `ring-test-runner` container ([`compose.test.yml`](compose.test.yml), profile `test`) against a separate CockroachDB. That file publishes the test node's HTTP port as 8008. The migration workflow applies every Alembic revision to an empty test database, because pytest builds schema from `ring/db/schema.sql`, not from Alembic.

A change to [`react/vite.config.ts`](react/vite.config.ts) or the bundler also needs a `vite preview` check in a browser, because `pnpm run build` alone has shipped a blank page.

Before you mark a behavior-changing PR ready, run [`.cursor/skills/verify-ring/SKILL.md`](.cursor/skills/verify-ring/SKILL.md) for the touched features. Keep proof under `/opt/cursor/artifacts/verify-ring/<run-id>/`. Do not attach images, recordings, or other binaries to the PR.

## Codebase

Domain packages use this shape:

```
ring/<domain>/
  api/        # FastAPI routers
  crud/       # SQLAlchemy queries / mutations
  models/     # SQLAlchemy ORM models
  schemas/    # Pydantic request/response schemas
```

- `ring/parties/` — users, groups, invites, group key/values
- `ring/letters/` — letters, questions, responses, default questions
- `ring/tasks/` — scheduling
- `ring/notifications/` — push/email subscriptions
- `ring/notebook/` — collaborative notebook (Y.js via pycrdt)
- `ring/search/` — search endpoints (CockroachDB vector index)
- `ring/auth/` — authentication routes
- `ring/authz/` — Casbin authorization ([`authz.py`](ring/authz/authz.py))
- `ring/api_identifier/` — `APIIdentified` mixin and `APIPrefix` ([`api_identified_model.py`](ring/api_identifier/api_identified_model.py))
- `ring/fastapp/` — app factory; routers are wired in [`routes.py`](ring/fastapp/routes.py)
- `ring/fastapp/_gen/` and `ring/search/_gen/` — generated import factories (`ring gen imports`)
- `ring/security.py` — password hashing and JWT access tokens
- `ring/alembic/` — migrations

Frontend under `react/src/`:

- `client/` — generated `@hey-api` SDK and TanStack Query hooks (`sdk.gen.ts`, `types.gen.ts`, `client.gen.ts`, `@tanstack/`)
- `components/` — feature components; `components/ui/` holds shadcn primitives
- `routes/` — TanStack Router file routes. [`routeTree.gen.ts`](react/src/routeTree.gen.ts) is written by the TanStack Router Vite plugin.
- `hooks/`, `lib/`, `util/` — shared frontend code

## Conventions

- Models addressable through the API extend `APIIdentified`, declare `API_ID_PREFIX` from `APIPrefix`, and register with `@register_api_class(APIPrefix.X)`. IDs look like `grp_<uuid>` and `lttr_<uuid>`. Look them up with `bulk_get_models` and `get_model`.
- Check permissions with the helpers in `ring/authz/authz.py`: `load_and_check`, `bulk_load_and_check`, `check`, `filter_to_authorized`, `bulk_can_or_inaccessible`. Copy the pattern of sibling routes in the same domain. See [`.cursor/skills/ring-authz-checklist/SKILL.md`](.cursor/skills/ring-authz-checklist/SKILL.md).
- Register every router in `ring/fastapp/routes.py`.
- Never hand-write API calls in the frontend. Run `ring fe regen` and use the generated hooks in `react/src/client/`.
- Decorator registries (`JOB_REGISTRY`, `SEARCH_REGISTRY`, `API_CLASS_REGISTRY`, `ALL_FACTORIES`) and SQLAlchemy `Base.metadata` fill on import. After adding a model, `@job_factory`, `@interval_job_factory`, `@register_search_function`, `@register_api_class`, or `@register_factory`, run `ring gen imports`.
- A secondary entity that attaches to many parent types stores the parent's `api_identifier` in `target_api_id` and is loaded with `bulk_get_models`. Use no polymorphic FKs. Prefer hard deletes over soft-delete columns unless a feature requires undo. A new prefix in `APIPrefix` is 3–6 characters.
- Do not assume features that are not there. The JWT access token lasts about a week ([`ring/security.py`](ring/security.py)) and there is no refresh-token flow. Add one only when asked, and document it then.
- Prefer existing timeout mechanisms (Nginx proxy timeouts, botocore, boto3, FastAPI) over custom middleware, including for long-running image uploads.

## Migrations and deploys

- Migrations must be additive. Drops and renames take two steps. Auto-deploy runs `alembic upgrade head` against CockroachDB Cloud unattended.
- After a table or column change, run `ring db autogenerate-schema` to refresh `ring/db/schema.sql`. Pytest builds from that dump, not from Alembic. `ring db generate` pins `ring/alembic/head`. Two concurrent migration PRs both rewrite that file and conflict, so a sibling cannot land as a second Alembic head.
- Land backend changes first. The frontend half of a stack can reach production minutes after merge while the API half is still rolling or paused. Land UI that consumes new OpenAPI only after the API is live. See [`.cursor/skills/ring-split-pr/SKILL.md`](.cursor/skills/ring-split-pr/SKILL.md).
- CI publishes `ring-api` images. Laptop `ring deploy prod` is not the normal ship path: it defaults to `ring-llm`, and `-i ring-api` continues only after confirmation, when CI or ECR is down. Do not build images on the EC2 host. There is no frontend image.
- Never run migrations against a cloud database URI from `ring cloud prod-db` mode.

## Do not edit by hand

- `ring/fastapp/_gen/`, `ring/search/_gen/`, and `ring/tests/factories/entrypoint/hydrate_registries.py`. Run `ring gen imports`.
- `react/src/client/`. Run `ring fe regen`.
- `react/src/routeTree.gen.ts`. The TanStack Router Vite plugin writes it. `ring fe regen` does not.
- `ring/vendor/genesis_idp`. It is vendored from neil/genesis. Recopy with `ring gen genesis-idp --from <genesis clone>`.

## PRs

- Split big changes: backend first, then `ring fe regen` and UI. Each PR must pass `ring check lint` and its tests alone. Land stacked PRs in order, rebasing the rest onto `dev` after each merge.
- Merge manually, squash and delete the branch. Ignore `aviator-app` comments and the `mergequeue` label.

## Skills

File-scoped style rules are in [`.cursor/rules/`](.cursor/rules/) (`python.mdc`, `react.mdc`).

[`.cursor/skills/`](.cursor/skills/) holds playbooks:

- `ring-add-backend-resource` — new domain endpoint, model, and CRUD
- `ring-regen-frontend-client` — refresh `react/src/client/` after API changes
- `ring-authz-checklist` — permission checks for new routes
- `ring-split-pr` — split backend and frontend into separate PRs
- `ring-db-migration` — generate or modify Alembic migrations
- `ring-cloud-dev` — Cloud VM bootstrap, health checks, and browser testing
- `ring-cloud-prod-db` — point cloud Vite and the API at CockroachDB Cloud
- `verify-ring` — drive the running app and capture evidence
