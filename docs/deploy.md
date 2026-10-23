# Deploy and production infrastructure

## Infrastructure and external services (production)

Local dev uses Docker Compose with a local CockroachDB container. **Production**
is a single EC2 host running the same Compose stack, plus managed services below.
Full topology, request flows, and Cloudflare/EC2 wiring:
[infrastructure.md](infrastructure.md). Continuous deploy path:
[continuous-deploy.md](continuous-deploy.md).

| Service | Identifier / endpoint | Code / config |
|---------|----------------------|---------------|
| Compute | EC2 + Docker Compose (`ring.neilsriv.tech`) | [compose.prod.yml](../compose.prod.yml), [prod.nginx.conf](../prod.nginx.conf) |
| Database | CockroachDB Cloud `ring-db` (not RDS) | `COCKROACH_DATABASE_URI` in server `.env` |
| S3 uploads | Bucket `rings3files` (`us-east-1`) | [ring/fastapp/config.py](../ring/fastapp/config.py) `BUCKET_NAME`; upload in [ring/letters/crud/response.py](../ring/letters/crud/response.py) |
| CDN | `du32exnxihxuf.cloudfront.net` | [ring/s3/models/s3_model.py](../ring/s3/models/s3_model.py) `qualified_s3_url` |
| Email (SES) | `us-east-1`, sender `ring@neilsriv.tech` | [ring/email_util.py](../ring/email_util.py) |
| Logs (CloudWatch) | Log group `/ring/prod` (`us-east-1`) | `logging:` blocks in [compose.prod.yml](../compose.prod.yml); viewing/IAM in [infrastructure.md](infrastructure.md) |
| Container registry | ECR Public `public.ecr.aws/z2k1e8p1/` | [dev_util/docker.py](../dev_util/docker.py), [dev_util/prod.sh](../dev_util/prod.sh), [dev_util/deploy_host.sh](../dev_util/deploy_host.sh) |
| Frontend hosting | Cloudflare Workers Builds (`ring-frontend`), auto-deploys every push to `dev` | [react/wrangler.jsonc](../react/wrangler.jsonc), [react/plugins/version-stamp.ts](../react/plugins/version-stamp.ts) |

Both halves of prod deploy themselves from `dev`: the frontend about
1–2 minutes after any push, the API about 2–3 minutes after a backend-touching
push (Publish ring-api → Deploy ring-api). Docs-only merges deploy nothing
for the API. `ring deploy status` prints what each is running.

Canonical deploy doc: [continuous-deploy.md](continuous-deploy.md).
Topology: [infrastructure.md](infrastructure.md).

Do not assume ECS, RDS, Route 53, Redis/Celery, Lambda, or Bedrock — none are
in the current prod path. Embeddings go through the optional `ring-llm`
microservice; background work uses in-process APScheduler, not Celery.

## Continuous deploy (agents)

Merges to `dev` ship themselves. Treat every backend-touching PR as a
prod deploy:

- **Additive migrations only.** Auto-deploy runs `alembic upgrade head`
  against CockroachDB Cloud with nobody watching. Drops/renames are
  two-step. CI gate: [`.github/workflows/check_migrations.yml`](../.github/workflows/check_migrations.yml) (also
  `ring db check-migrations` / `ring db check-schema-drift` /
  `ring db check-alembic-head` locally). After a migration that changes
  tables/columns, refresh `ring/db/schema.sql` with
  `ring db autogenerate-schema` — pytest builds from that dump, not from
  Alembic. Pin `ring/alembic/head` to the new revision (`ring db generate`
  does this). Two concurrent migration PRs both rewrite that file and
  git-conflict, so a sibling cannot land as a second Alembic head.
- **Backend-first PRs** ([`ring-split-pr`](../.cursor/skills/ring-split-pr/SKILL.md)).
  Frontend deploys within minutes of merge; OpenAPI-consuming UI must
  land only after the API change is live (check
  `https://ring.neilsriv.tech/api/v1/version` / `ring deploy status`).
- **Do not invent laptop `ring deploy prod` for `ring-api`.** CI publishes
  images. That command defaults to `ring-llm` and confirms before
  building `ring-api`, which is the break-glass path when CI or ECR is down.
  There is no frontend image — the SPA ships only
  via Cloudflare Workers Builds. Host rollout is
  [`dev_util/deploy_host.sh`](../dev_util/deploy_host.sh) / Actions → **Deploy ring-api**.
- **Incident freeze:** repo variable `DEPLOY_PAUSED=true` stops automatic
  EC2 rollouts; manual Deploy still works for rollback. Pick a prior SHA
  with `ring deploy history` (or `ring deploy status` for what's live).
- **Never** build images on the EC2 host or attach `ring.neilsriv.tech`
  as a Cloudflare Worker custom domain (use Workers Routes with `/api/*`
  and `/.well-known/*` passthrough — see [continuous-deploy.md](continuous-deploy.md)).
- Bundler / [`react/vite.config.ts`](../react/vite.config.ts) build changes need a `vite preview` browser
  check; `pnpm run build` alone has shipped a blank runtime page.
