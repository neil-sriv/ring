# Continuous deploy plan

**North star: every merge to `dev` deploys to production, lightning fast.**

Target: a merge that touches `react/` is live in ~2 minutes, a merge that
touches `ring/` is live in ~2–3 minutes, docs-only merges deploy nothing.
No laptop builds, no SSH-by-hand, rollback is one command.

Status legend: `[ ]` todo · `[x]` done. Update this file as phases land.

---

## Where we are today

| Piece | State |
|-------|-------|
| Frontend PR previews | ✅ Cloudflare Workers Builds deploys every branch; PR comments carry preview URLs (see [infrastructure.md](infrastructure.md)) |
| Frontend prod | Static build served by nginx on EC2; deployed manually via `ring deploy prod` |
| Backend prod | `ring-api` image built **on a laptop**, pushed to ECR Public `:latest`, pulled + restarted by hand on EC2 |
| Migrations | `ring db upgrade` run by hand on EC2 |
| Version introspection | ✅ `GET /api/v1/version` returns git SHAs + image digests (#298) — the smoke-check hook for deploy gating |
| CORS for previews | ✅ `BACKEND_CORS_ORIGIN_REGEX` live on prod (#295) |

Known risks of the current flow (both bit us on 2026-08-11):

- Laptop builds deploy whatever is checked out locally, reviewed or not.
- `:latest`-only tags mean no rollback artifact.

---

## Phase 1 — Frontend cutover to Cloudflare (independent, reversible)

Outcome: merges to `dev` deploy the prod frontend automatically. This is
the first half of the north star and needs no backend work.

- [ ] Set `PYTHON_VERSION=3.13.3` build variable on the `ring-frontend`
      Worker (kills a ~4 min Python install triggered by the repo-root
      `.python-version`; see infrastructure.md).
- [ ] **Route split — never attach the domain to the Worker directly.**
      A custom domain would swallow `/api/v1/*` (this took prod down
      briefly on 2026-08-11). Instead, in the Cloudflare zone
      (dash → `neilsriv.tech` → Workers Routes) add, in this order:
      1. `ring.neilsriv.tech/api/*` → Worker: **None** (passthrough to
         EC2 nginx — keeps WebSockets and 500MB uploads on nginx)
      2. `ring.neilsriv.tech/.well-known/*` → Worker: **None**
         (**required while certbot remains**: the HTTP-01 renewal
         challenge flows through the proxy to nginx; without this
         exclusion the Let's Encrypt cert silently stops renewing.
         Skip/remove this route once the Origin CA swap below is done.)
      3. `ring.neilsriv.tech/*` → `ring-frontend`
      More-specific routes win, but add the exclusions first anyway so
      there is no window where `/*` is live alone.
- [ ] **Replace Let's Encrypt with a Cloudflare Origin CA cert**
      (recommended — the domain is orange-clouded, so the origin cert
      only secures the Cloudflare→EC2 hop and certbot is pure overhead):
      1. Dash → zone → SSL/TLS → **Origin Server** → Create Certificate
         (hostnames `ring.neilsriv.tech` + `www.ring.neilsriv.tech`,
         15-year validity)
      2. Install cert+key on EC2, point `ssl_certificate` /
         `ssl_certificate_key` in `prod.nginx.conf` at them, restart
         nginx
      3. SSL/TLS overview → set mode to **Full (strict)** (Origin CA
         certs validate under strict)
      4. Remove the `certbot` service/profile and letsencrypt mounts
         from `compose.prod.yml`, the `/.well-known/acme-challenge/`
         location in `prod.nginx.conf`, and route 2 above
      Caveat: Origin CA certs are trusted **only by Cloudflare** — any
      direct-to-origin HTTPS access (gray-clouding the DNS record,
      `curl --resolve` at the EC2 IP) will fail cert validation. Keep
      that in mind when debugging.
- [ ] `www.ring.neilsriv.tech`: if its DNS record is proxied, either add
      the same three routes for `www.` or leave it on nginx during the
      soak.
- [ ] Verify:
      - `curl -s -o /dev/null -w "%{http_code}" -H "Sec-Fetch-Mode: navigate" https://ring.neilsriv.tech/some-spa-route`
        → `200` (Worker SPA fallback; without the header a `404` here is
        normal and confirms the Worker, not nginx, answered)
      - `curl -s https://ring.neilsriv.tech/api/v1/version` → JSON from
        FastAPI (route 1 works)
      - `curl -s -o /dev/null -w "%{http_code}" http://ring.neilsriv.tech/.well-known/acme-challenge/probe`
        → `404` from nginx, **not** HTML from the Worker (route 2 works)
      - Notebook WebSocket + an image upload in the browser
      - PWA: hard-refresh an existing session, confirm it updates
      Rollback = delete route 3 (`/*`); nginx still serves the old
      frontend underneath throughout the soak.
- [ ] Soak for a few days, then clean up:
      - [ ] Remove `frontend` service from `compose.prod.yml`
      - [ ] Remove `location / { proxy_pass http://ring-frontend:80/; }`
            from `prod.nginx.conf` (keep the `serviceWorker.js` /
            `manifest.webmanifest` aliases only if still needed)
      - [ ] `ring deploy prod` drops the `ring-frontend` image
      - [ ] Update [infrastructure.md](infrastructure.md) topology

Note on same-origin: with the route split, prod frontend and API share
`ring.neilsriv.tech`, so prod needs **no CORS change**. The
`BACKEND_CORS_ORIGIN_REGEX` stays only for `*.workers.dev` previews.

---

## Phase 2 — CI builds backend images (ends laptop builds)

Outcome: every `dev` push produces a reproducible, SHA-tagged `ring-api`
image. Deploys still manual, but from CI artifacts only.

- [ ] GitHub Actions workflow on push to `dev` with
      `paths: [ring/**, pyproject.toml, uv.lock, ring/ring.Dockerfile, compose*.yml]`
- [ ] Build with BuildKit + registry cache so the `uv sync` layer is
      reused unless `uv.lock` changed; code-only merges rebuild one thin
      layer (~60–90s including push)
- [ ] Push tags `:latest` **and** `:<git-sha>` (registry: keep ECR
      Public, or move to GHCR — decide below)
- [ ] `dev_util/prod.sh` accepts an optional SHA argument and pulls that
      tag instead of `:latest`
- [ ] Rollback recipe documented: `prod.sh <previous-sha>` + `up -d`

## Phase 3 — Push-button backend deploy

Outcome: deploying is a `workflow_dispatch` click with a green/red result.

- [ ] Deploy job: connect to EC2 (SSH key in repo secrets, or AWS SSM
      Session Manager for keyless), then on the box:
      1. `dev_util/prod.sh <sha>` (pull images)
      2. `docker compose ... run --rm api alembic upgrade head`
         (migrations run from the box — the CockroachDB Cloud URI never
         leaves the server `.env`)
      3. `docker compose ... up -d api`
      4. Gate: curl `GET /api/v1/version`, assert deployed SHA; on
         failure, auto-rollback to previous SHA and fail the run
- [ ] Actions `concurrency` group `prod-deploy` (queue, don't cancel) so
      two merges can't race migrations
- [ ] Gate deploy on backend tests (suite is ~26s in-container; worth it)

## Phase 4 — Flip to continuous (the north star)

- [ ] Change trigger from `workflow_dispatch` to `push: branches: [dev]`
      after several clean push-button runs
- [ ] Remove `--reload` from the prod uvicorn command in
      `compose.prod.yml` (file-watching wastes RAM on the 1GB box;
      deploys are image swaps now)
- [ ] Retire `ring deploy prod` for everything except `ring-llm`
- [ ] Update [infrastructure.md](infrastructure.md) deployment section

### Per-merge behavior once complete

| Merge touches | What runs | Time to live |
|---------------|-----------|--------------|
| `react/` only | Cloudflare Worker build + deploy | ~2 min |
| `ring/` only | tests → image build → EC2 swap | ~2–3 min |
| both | both tracks in parallel | ~3 min |
| docs only | nothing | 0 |

---

## Rules that make auto-deploy safe

1. **Migrations must be additive / backwards-compatible.** They auto-run
   against CockroachDB Cloud with no human watching. Destructive changes
   (drops, renames) are two-step: deploy code that stops using the
   column, then a later migration removes it.
   - [ ] Add a CI gate that runs `alembic upgrade head` against the test
         CockroachDB so broken revisions can't merge.
2. **Backend-first PRs remain law** (see `ring-split-pr` skill). The
   frontend track deploys within minutes of merge; an OpenAPI-consuming
   frontend change must merge only after the API change is deployed.
3. **Prod-build browser check for bundler changes.** Any PR touching
   `vite.config.ts` build options gets a `vite preview` browser check
   (the 2026-08-11 blank-page incident shipped through `pnpm run build`
   passing while the bundle crashed at runtime).

## Open decisions

- [ ] Registry: stay on ECR Public vs move backend images to GHCR
      (GHCR needs no AWS creds in Actions — `GITHUB_TOKEN` suffices —
      but EC2 then needs a pull token for private images)
- [ ] EC2 access from Actions: SSH key secret vs AWS SSM Session Manager
- [ ] Whether `ring-llm` ever joins CD (heavy image; suggest: no, manual)
- [ ] Whether to keep an escape hatch (`VITE_MAINTENANCE_MODE` fast path
      or a `deploy:pause` label) for freezing auto-deploys during
      incidents

## Constraints

- The EC2 `t2.micro` (1GB RAM) must never build images; CI builds, the
  box only pulls.
- Cloudflare free-plan proxy caps request bodies at 100MB. The domain is
  already orange-clouded, so this cap applies today; the route split
  does not change it.
