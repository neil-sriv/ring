# Continuous deploy

**Every merge to `dev` can ship to production.** Frontend rebuilds on
*any* push to `dev` (~1–2 minutes). Backend-touching merges also publish
and roll out the API (~2–3 minutes). Docs/skills-only merges skip the
API track entirely — they still redeploy an identical frontend bundle.

This is the live prod path. Topology and Cloudflare/EC2 wiring live in
[infrastructure.md](infrastructure.md). Agent-facing rules are summarized
in [AGENTS.md](../AGENTS.md).

---

## Per-merge behavior

| Merge touches | What runs | Time to live |
|---------------|-----------|--------------|
| `react/` only | Cloudflare Workers Builds → Worker deploy | ~1–2 min |
| `ring/` (and related backend paths) | Publish ring-api → tests + migrations → EC2 swap | ~2–3 min |
| both | both tracks in parallel | ~3 min |
| docs / skills / non-backend only | nothing for API; frontend still rebuilds on any `dev` push | ~1–2 min |

Backend path filter for publish (also inherited by auto-deploy):

`ring/**`, `pyproject.toml`, `uv.lock`, `compose.core.yml`,
`compose.prod.yml`, `.github/workflows/publish_api.yml`.

---

## Architecture (two independent tracks)

```
dev push
 ├─ react/** (any push, actually) ──► Cloudflare Workers Builds ──► ring-frontend Worker
 │                                      ring.neilsriv.tech/*  (routes)
 │
 └─ backend paths ──► Publish ring-api ──► ECR :latest + :<sha>
                         │
                         └─ (on success) Deploy ring-api
                              ├─ pytest (target SHA)
                              ├─ alembic upgrade head + schema drift check
                              └─ SSH → deploy_host.sh --rollback-on-fail <sha>
                                   └─ EC2: git checkout -f, prod.sh, migrate, compose up, /version gate
```

Frontend and API share `ring.neilsriv.tech` via Cloudflare Workers Routes:

1. `ring.neilsriv.tech/api/*` → passthrough (nginx / API / WebSockets)
2. `ring.neilsriv.tech/.well-known/*` → passthrough (Let's Encrypt ACME)
3. `ring.neilsriv.tech/*` → `ring-frontend` Worker

Never attach the custom domain directly to the Worker — that swallows
`/api/*` and takes the API down.

Prod API runs the **image filesystem** (no `./ring` bind-mount, no
uvicorn `--reload`). The host git checkout only supplies compose, nginx,
and `.env`. Migrations run *inside* the API container.

---

## Workflows and scripts

| Piece | Path |
|-------|------|
| Publish images | [`.github/workflows/publish_api.yml`](../.github/workflows/publish_api.yml) |
| Deploy (auto + manual) | [`.github/workflows/deploy_api.yml`](../.github/workflows/deploy_api.yml) |
| Migration + schema drift gate | [`.github/workflows/check_migrations.yml`](../.github/workflows/check_migrations.yml) |
| Host rollout | [`dev_util/deploy_host.sh`](../dev_util/deploy_host.sh) / `uv run ring deploy host` |
| Image pull only | [`dev_util/prod.sh`](../dev_util/prod.sh) |
| What is live | `uv run ring deploy status` |

### Deploy job shape

1. Resolve SHA (`workflow_run.head_sha`, or dispatch input, or `github.sha`)
2. Fail fast if `public.ecr.aws/z2k1e8p1/ring-api:<sha>` is missing
3. Run backend tests and `check_migrations` for that SHA
4. SSH to EC2 and run `./dev_util/deploy_host.sh --rollback-on-fail <sha>`

Concurrency group `prod-deploy` **queues** (does not cancel) so two
deploys cannot race migrations.

Auto-deploy uses `workflow_run` on **Publish ring-api** completing — not
`push: dev`. A push trigger would race the image build. Failed publishes
never deploy (`conclusion == 'success'`).

`deploy_host.sh` force-checkouts tracked files (`git checkout -f -B`) so
host-side drift like a rewritten `uv.lock` cannot abort the deploy.
Untracked files (`.env`) are left alone.

---

## Secrets and variables

| Name | Kind | Purpose |
|------|------|---------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | secret | Publish to ECR Public |
| `PROD_SSH_HOST` | secret | EC2 public IP or **gray-cloud** DNS — not orange `ring.neilsriv.tech` (Cloudflare will not forward SSH) |
| `PROD_SSH_USER` | secret | Linux user on the box (`ubuntu` / `ec2-user`) |
| `PROD_SSH_KEY` | secret | Dedicated deploy **private** key (ed25519). Not a laptop key. Set with `gh secret set PROD_SSH_KEY < ~/.ssh/ring-prod-deploy` |
| `PROD_SSH_PORT` | variable | Optional; default `22` |
| `PROD_APP_DIR` | variable | Optional; default `$HOME/ring` |
| `DEPLOY_PAUSED` | variable | Set to `true` to freeze **automatic** deploys |

### Freezing auto-deploy

```text
Settings → Secrets and variables → Actions → Variables
DEPLOY_PAUSED = true
```

Merges still publish images; they do not roll out. Manual **Deploy
ring-api** is deliberately *not* blocked, so rollback stays one click.
Delete the variable (or set it to anything other than `true`) to resume.

Longer term, OIDC + SSM `SendCommand` would remove the standing SSH key;
SSH is the current path.

---

## Rollback

```bash
# Preferred: Actions → Deploy ring-api, sha = previous published image SHA
# Or on the box:
./dev_util/deploy_host.sh <previous-published-sha>
# Image-only restore without changing compose checkout:
./dev_util/deploy_host.sh --skip-git <previous-published-sha>
```

`--rollback-on-fail` captures live `image_build.sha` *before* mutating
and restores that image if `/api/v1/version` does not match after swap.

The SHA must exist as `ring-api:<sha>` in ECR (a Publish ring-api run).
Docs-only `origin/dev` tips often have **no** image tag.

---

## Verify what is live

```bash
uv run ring deploy status
curl -sS -A 'ring/1.0' https://ring.neilsriv.tech/version.json       # frontend
curl -sS -A 'ring/1.0' https://ring.neilsriv.tech/api/v1/version     # API
```

Use a non-default User-Agent — Cloudflare rejects Python-urllib's default
with 1010/403. In the app: **Settings → Build**.

For the API, `image_build.sha` is the running code (baked into the image).
`git` is unavailable in prod after the image-filesystem cutover.

---

## Laptop / break-glass builds

CI publishes `ring-api`. Frontend prod is Cloudflare.

```bash
ring deploy prod -i ring-llm                  # still manual
ring deploy prod -i ring-api -t "$(git rev-parse HEAD)"   # confirms first
```

`ring deploy prod` defaults to `ring-llm` and prompts before building
`ring-api` / `ring-frontend`. Prefer CI unless ECR or Actions is down.

---

## Safety rules (required for auto-deploy)

1. **Migrations must be additive / backwards-compatible.** They run
   unattended against CockroachDB Cloud. Destructive changes are
   two-step: deploy code that stops using the column, then a later
   migration drops it.
2. **CI proves the revision chain.** `check_migrations.yml` applies
   every Alembic revision to an empty test CockroachDB and compares
   table/column names to `ring/db/schema.sql` (pytest builds from that
   dump). After adding a migration, run `ring db autogenerate-schema`
   when the dump should change.
3. **Backend-first PRs** ([`ring-split-pr`](../.cursor/skills/ring-split-pr/SKILL.md)).
   The frontend track deploys within minutes of merge; OpenAPI-consuming
   UI must land only after the API change is live.
4. **Bundler / Vite config changes** need a `vite preview` browser check
   — `pnpm run build` alone has shipped a blank page that crashed at
   runtime.
5. **Never build images on the EC2 `t2.micro`.** CI builds; the box only
   pulls.
6. **Vector index cluster setting** is out-of-band
   (`feature.vector_index.enabled`) — set in test CI, `conftest.py`, and
   `cloud-start.sh`. Migrations that create vector indexes assume it.

`ring-llm` does **not** join CD (heavy / inactive).

---

## Optional leftovers (not required for CD)

Prod SPA already comes from Cloudflare. These only tidy EC2:

- Delete unused `www.ring.*` Workers Routes or add DNS
- Remove leftover `frontend` service from `compose.prod.yml` (~300MB)
- Remove nginx SPA `proxy_pass` to `ring-frontend`
- Drop `ring-frontend` from `IMAGE_TAG_NAMES` if unused

---

## How we got here (phases)

| Phase | Outcome | Status |
|-------|---------|--------|
| 1 | Cloudflare Workers Routes for prod SPA | Done |
| 2 | CI SHA-tagged `ring-api` images on `dev` | Done (#303) |
| 3 | Push-button `Deploy ring-api` + `deploy_host.sh` | Done (#333) |
| 4 | Auto-deploy after successful publish | Done (#334) |
| 5 | Optional EC2 frontend cleanup | Open |

Incidents that shaped the design: attaching the domain to the Worker
(swallowed `/api`); ECR cache needing OCI single-manifest export;
image-only rollback while `./ring` was still bind-mounted; `--skip-git`
compose sync silently corrupting the host checkout; Cockroach
`/health?ready=1` going green before SQL auth worked; host `uv.lock`
drift aborting plain `git checkout`.
