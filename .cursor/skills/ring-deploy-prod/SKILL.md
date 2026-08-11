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

This does **not** restart EC2. Host rollout is
[`dev_util/deploy_host.sh`](../../../dev_util/deploy_host.sh) (Phase 3
will have Actions call that script).

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

## Host rollout

```bash
cd ring
./dev_util/deploy_host.sh                 # origin/dev + :latest
./dev_util/deploy_host.sh <sha>           # pin / rollback
# uv run ring deploy host --rollback-on-fail <sha>
```

The script: fetch + `git checkout -B dev <sha>`, `prod.sh <sha>`,
`uv run ring db upgrade`, compose `up -d --force-recreate`, then gate
on `GET /api/v1/version` (`git.sha` and `image_build.sha`). Do not skip
`--force-recreate` yourself — the script already passes it.

`prod.sh` is image-pull only. Do not treat it as a full rollback while
`./ring` is bind-mounted with `--reload`.

## Notes

- Prod SPA and API share `ring.neilsriv.tech` via Cloudflare route split
  (`/api/*` and `/.well-known/*` passthrough). No extra CORS for prod.
- Image/registry names live in `dev_util/docker.py`.
- Builds bake git SHA into `RING_BUILD_GIT_*` via `dev_util/git_meta.py`.
