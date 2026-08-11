---
name: ring-deploy-prod
description: Build and ship Ring's production API image to public ECR, or pull a SHA-tagged image on the EC2 host. Use when the user asks to deploy to prod, push the API image, release, publish ring-api, or roll back a backend deploy.
---

# Deploying Ring to prod

Frontend prod is Cloudflare Workers Builds + Workers Routes (see
[docs/infrastructure.md](../../../docs/infrastructure.md) and PR #301).
Backend images live in `public.ecr.aws/z2k1e8p1/ring-api`. `ring-llm` is
manual and currently inactive. Do not build `ring-frontend` unless rolling
the SPA back onto nginx.

## Preferred: CI publish

Pushes to `dev` that touch `ring/**` (or **Actions → Publish ring-api**)
run [`.github/workflows/publish_api.yml`](../../../.github/workflows/publish_api.yml):

1. Build `linux/amd64` from `ring/ring.Dockerfile` with registry layer cache.
2. Push `:latest` and `:<git-sha>`.

This does **not** restart EC2. Host pull is still manual (Phase 3 of the
CD plan).

Requires GitHub secrets `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
from a dedicated IAM user — not laptop keys.

## Laptop fallback

```bash
ring deploy prod
# SHA tag (same as CI):
ring deploy prod -t "$(git rev-parse HEAD)"
```

Default image is `ring-api`. Pass `-i ring-frontend` / `-i ring-llm` only
when you really need those images.

## Host pull

```bash
cd ring
git checkout dev && git pull origin dev
./dev_util/prod.sh                 # ring-api:latest
# ./dev_util/prod.sh <git-sha>     # pin / rollback
ring db upgrade                    # if this commit has a migration
ring compose any --profile prod up -d --force-recreate
```

Do not skip `--force-recreate`: compose keeps the old container when the
local tag name (`prod-ring-api:latest`) is unchanged.

Verify:

```bash
curl -sS https://ring.neilsriv.tech/api/v1/version
```

## Notes

- Prod SPA and API share `ring.neilsriv.tech` via Cloudflare route split
  (`/api/*` and `/.well-known/*` passthrough). No extra CORS for prod.
- Image/registry names live in `dev_util/docker.py`.
- Builds bake git SHA into `RING_BUILD_GIT_*` via `dev_util/git_meta.py`.
