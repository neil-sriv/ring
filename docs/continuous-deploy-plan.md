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
| Frontend prod | ✅ Cloudflare Workers Routes (`/*`); `/api/*` and `/.well-known/*` passthrough to EC2 nginx. Leftover `ring-frontend` container still runs as a rollback hatch (Phase 5 cleanup) |
| Backend images | ✅ CI publishes `ring-api:latest` + `:<git-sha>` to ECR Public on `dev` pushes (#303) |
| Backend rollout | ✅ Image filesystem (#309, live 2026-08-11: `image_build.sha=195c464`, `git.source=unavailable`). Host script is still run by hand; Actions job not built yet |
| Migrations | Run by `deploy_host.sh` (`uv run ring db upgrade --profile prod`) |
| Version introspection | ✅ `GET /api/v1/version` returns git SHAs + image digests (#298) — verified 2026-08-11 after the #303 swap (`image_build.source=image_env`) |
| CORS for previews | ✅ `BACKEND_CORS_ORIGIN_REGEX` live on prod (#295) |

Known remaining risks:

- Host pull is still manual; a green publish does not restart prod.

---

## Phase 1 — Frontend cutover to Cloudflare (independent, reversible)

Outcome: merges to `dev` deploy the prod frontend automatically. This is
the first half of the north star and needs no backend work.
*(required work done 2026-08-11; leftover nginx SPA is optional Phase 5)*

- [x] Set `PYTHON_VERSION=3.13.3` build variable on the `ring-frontend`
      Worker (kills a ~4 min Python install triggered by the repo-root
      `.python-version`; see infrastructure.md). *(done 2026-08-11)*
- [x] **Route split — never attach the domain to the Worker directly.**
      A custom domain would swallow `/api/v1/*` (this took prod down
      briefly on 2026-08-11). Instead, in the Cloudflare zone
      (dash → `neilsriv.tech` → Workers Routes) add, in this order:
      1. `ring.neilsriv.tech/api/*` → Worker: **None** (passthrough
         keeps WebSockets on nginx/origin and avoids Worker handling
         of `/api/*`; upload size stays the existing Cloudflare plan
         limit of 100MB — route split does not restore nginx's 500MB)
      2. `ring.neilsriv.tech/.well-known/*` → Worker: **None**
         (**required**: certbot's HTTP-01 renewal challenge flows
         through the proxy to nginx; without this exclusion the
         Let's Encrypt cert silently stops renewing)
      3. `ring.neilsriv.tech/*` → `ring-frontend`
      More-specific routes win, but add the exclusions first anyway so
      there is no window where `/*` is live alone.
      *(done 2026-08-11 — all three routes live and verified)*

      Considered and rejected: swapping Let's Encrypt for a Cloudflare
      Origin CA cert (15-year, no certbot). Rejected because Origin CA
      certs are trusted only by Cloudflare, so any direct-to-origin
      HTTPS access (gray-clouding the record, `curl --resolve` at the
      EC2 IP) fails cert validation. Keeping Let's Encrypt preserves a
      browser-valid origin, at the cost of keeping certbot and route 2.
- [x] Verify: *(curl checks done 2026-08-11 — Worker serves `/*`
      [content-hash etags match workers.dev], API + version endpoint
      via route 1, acme webroot reachable over http; browser soak
      checks — notebook WS, upload, PWA refresh — ongoing)*
      - `curl -s -o /dev/null -w "%{http_code}" -H "Sec-Fetch-Mode: navigate" https://ring.neilsriv.tech/some-spa-route`
        → `200` (Worker SPA fallback; without the header a `404` here is
        normal and confirms the Worker, not nginx, answered)
      - `curl -s https://ring.neilsriv.tech/api/v1/version` → JSON from
        FastAPI (route 1 works)
      - `curl -s -o /dev/null -w "%{http_code}" http://ring.neilsriv.tech/.well-known/acme-challenge/probe`
        → `404` from nginx (route 2 works). Note: over **https** this
        path returns the app HTML — that is *not* the Worker; nginx's
        443 server has no acme location, so it falls into the
        `location /` frontend proxy. Verified via Cloudflare Trace
        (2026-08-11): the Worker is correctly disabled on the route.
        Only the http path matters for ACME, and it hits the webroot.
        Ambiguity disappears after cleanup removes the frontend proxy.
      - Notebook WebSocket + an image upload in the browser
      - PWA: hard-refresh an existing session, confirm it updates
      Rollback = delete route 3 (`/*`); nginx still serves the old
      frontend underneath (kept on purpose until Phase 5).

Note on same-origin: with the route split, prod frontend and API share
`ring.neilsriv.tech`, so prod needs **no CORS change**. The
`BACKEND_CORS_ORIGIN_REGEX` stays only for `*.workers.dev` previews.

---

## Phase 2 — CI builds backend images (ends laptop builds)

Outcome: every `dev` push produces a reproducible, SHA-tagged `ring-api`
image. Deploys still manual, but from CI artifacts only.
*(done 2026-08-11 via #303; first CI image verified on EC2)*

- [x] GitHub Actions workflow on push to `dev` with
      `paths: [ring/**, pyproject.toml, uv.lock, compose.core.yml, compose.prod.yml, .github/workflows/publish_api.yml]`
      — [`.github/workflows/publish_api.yml`](../.github/workflows/publish_api.yml)
      (#303, merged 2026-08-11). Also `workflow_dispatch`.
- [x] Build with BuildKit + registry cache (`:buildcache` with
      `image-manifest=true,oci-mediatypes=true` so ECR accepts the
      cache). Deps are copied before the rest of the tree so code-only
      merges reuse the `requirements.txt` layer.
- [x] Push tags `:latest` **and** `:<git-sha>` to ECR Public
      (`public.ecr.aws/z2k1e8p1/ring-api`). Staying on ECR Public
      (EC2 already pulls it with no extra token).
- [x] `dev_util/prod.sh` accepts an optional SHA argument and defaults
      to `ring-api` only. Laptop fallback: `uv run ring deploy prod`
      (also API-only by default).
- [x] Rollback recipe documented (README, infrastructure.md,
      `deploy_host.sh` / `prod.sh --help`). Prefer
      `./dev_util/deploy_host.sh <previous-sha>` (#308). Image-only
      `prod.sh` is a code rollback after the #309 cutover.
- [x] Prod smoke after merge: `GET /api/v1/version` went from
      `image_build.source=unavailable` to `image_env` with
      `sha=9e7fd0bf…` and a new API `image_id`. Frontend/llm images
      unchanged (expected).

## Phase 3 — Push-button backend deploy

Outcome: deploying is one script on the box (and later a
`workflow_dispatch` click that runs that script). Do **not** have
Actions SSH a pile of commands — the host script is the interface.

Image-filesystem cutover *(done 2026-08-11 via #309; applied on EC2)*:

- [x] Stop mounting `./ring` and `./.git` into the prod API container
      (bind-mounts stay in `compose.dev.yml` for local `--reload`)
- [x] Drop uvicorn `--reload` from `compose.prod.yml`
- [x] Version gate asserts `image_build.sha` only. `--rollback-on-fail`
      captures live `image_build.sha` before mutating and restores
      that image with `--skip-git`
      Live `/version` after apply: `image_build.sha=195c464` (#309),
      `git.source=unavailable`, new API `image_id`.

- [x] Host script: [`dev_util/deploy_host.sh`](../dev_util/deploy_host.sh)
      / `uv run ring deploy host [sha]` (#308, merged 2026-08-11).
      On the box it:
      1. `git fetch` + `git checkout -B dev <sha>` (compose/nginx on
         disk; running Python is the image)
      2. `./dev_util/prod.sh <sha>` (image pull only)
      3. `uv run ring db upgrade --profile prod` (Cockroach URI never
         leaves the server `.env`)
      4. `uv run ring compose any --profile prod up -d --force-recreate`
      5. Gate: curl `GET /api/v1/version`, assert `image_build.sha`.
         `--rollback-on-fail` restores the pre-deploy image SHA
      Rollback: `./dev_util/deploy_host.sh <previous-sha>`
      First EC2 run 2026-08-11: `0f1871c` (#308) has no image
      (docs/script-only; `publish_api.yml` did not run). Deployed
      `60ca61b` (#306, last Publish ring-api SHA). Afterward
      `/version` was `git.sha=0f1871c` (checkout) +
      `image_build.sha=60ca61b` (image). Pass a published SHA, not
      `HEAD`, when `origin/dev` did not touch `ring/**`.
- [ ] Deploy job: connect to EC2 (SSH key in repo secrets, or AWS SSM
      Session Manager for keyless) and run
      `./dev_util/deploy_host.sh --rollback-on-fail <sha>`
- [ ] Actions `concurrency` group `prod-deploy` (queue, don't cancel) so
      two merges can't race migrations
- [ ] Gate deploy on backend tests (suite is ~26s in-container; worth it)

## Phase 4 — Flip to continuous (the north star)

- [ ] Change trigger from `workflow_dispatch` to `push: branches: [dev]`
      after several clean push-button runs
- [ ] Stop checking out git on the host during deploy (`deploy_host.sh
      --skip-git`) once the bind-mount is gone
- [ ] Retire `ring deploy prod` for everything except `ring-llm`
- [ ] Update [infrastructure.md](infrastructure.md) deployment section

### Per-merge behavior once Phase 4 is complete

| Merge touches | What runs | Time to live |
|---------------|-----------|--------------|
| `react/` only | Cloudflare Worker build + deploy | ~2 min |
| `ring/` only | tests → image build → EC2 swap | ~2–3 min |
| both | both tracks in parallel | ~3 min |
| docs only | nothing | 0 |

## Phase 5 — Optional frontend leftover cleanup

Not required for CD. Prod already serves the SPA from Cloudflare.
These only tidy the EC2 fallback and unused `www.ring` routes.

- [ ] `www.ring.neilsriv.tech`: routes exist but **no DNS record does**
      (`www.neilsriv.tech` is a different, unrelated record). Either add
      a proxied CNAME `www.ring` → `ring.neilsriv.tech`, or delete the
      three `www.ring.*` routes.
- [ ] Remove `frontend` service from `compose.prod.yml` (frees ~300MB
      on the t2.micro). After this, rollback is "delete route 3" only
      if you re-add the container, so do this once the Worker soak
      feels boring.
- [ ] Remove `location / { proxy_pass http://ring-frontend:80/; }`
      from `prod.nginx.conf` (keep the `serviceWorker.js` /
      `manifest.webmanifest` aliases only if still needed). Also add
      an https `/.well-known/` location if you want ACME to work on
      443 without falling into `location /`.
- [ ] `uv run ring deploy prod` / `prod.sh` already default to
      `ring-api` only; drop `ring-frontend` from `IMAGE_TAG_NAMES` if
      nothing else references it.
- [ ] Update [infrastructure.md](infrastructure.md) topology (nginx
      no longer serves the SPA).

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

- [x] Registry: **stay on ECR Public** (`public.ecr.aws/z2k1e8p1/`).
      Decided in #303 — EC2 already pulls public images with no token.
      GHCR would need a pull credential on the box.
- [x] EC2 access from Actions: **SSH** (`PROD_SSH_HOST` / `PROD_SSH_USER` /
      `PROD_SSH_KEY`), same shape as superseded #290. SSM still possible
      later; not required to get push-button deploys.
- [x] `ring-llm` does **not** join CD (heavy image; still manual / inactive)
- [ ] Whether to keep an escape hatch (`VITE_MAINTENANCE_MODE` fast path
      or a `deploy:pause` label) for freezing auto-deploys during
      incidents

## Constraints

- The EC2 `t2.micro` (1GB RAM) must never build images; CI builds, the
  box only pulls.
- Cloudflare free-plan proxy caps request bodies at 100MB. The domain is
  already orange-clouded, so this cap applies today; the route split
  does not change it.
