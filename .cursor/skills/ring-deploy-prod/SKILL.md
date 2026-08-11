---
name: ring-deploy-prod
description: Build and ship Ring's production backend images to public ECR. Use when the user asks to deploy to prod, push prod images, release, or rebuild/publish the api or llm images to public.ecr.aws. The frontend deploys via Cloudflare, not this flow.
---

# Deploying Ring to prod

Prod backend runs from images published to the public ECR registry
`public.ecr.aws/z2k1e8p1/` (`ring-api`, `ring-llm`). Deploying means
building those images locally, authenticating to ECR, and pushing them.

**The frontend is NOT deployed this way.** It is served by the Cloudflare
Worker `ring-frontend`, auto-deployed by Cloudflare Workers Builds on
every merge to `dev` that touches `react/`. See the "Frontend PR
previews" section of [docs/infrastructure.md](../../../docs/infrastructure.md)
and [docs/continuous-deploy-plan.md](../../../docs/continuous-deploy-plan.md).

## One command

```bash
ring deploy prod
```

This runs, in order:

1. `compose --profile prod build` — build the prod backend images.
2. `aws ecr-public get-login-password | docker login … public.ecr.aws` —
   authenticate Docker against public ECR (`us-east-1`).
3. `ring docker tp` — tag the `prod-*` images and push them to ECR.

### Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--region` | `us-east-1` | AWS region for the ECR login |
| `--skip-login` | off | Skip step 2 if already logged in |

## Manual equivalent

```bash
uv run ring compose any --profile prod build
aws ecr-public get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin public.ecr.aws
uv run ring docker tp
```

Restrict to specific images with `-i`, e.g. `ring docker tp -i ring-api`.

## Prerequisites

- AWS CLI configured with credentials that can push to `public.ecr.aws/z2k1e8p1/`.
- Docker running and able to build `linux/amd64` images (prod compose pins
  `platform: linux/amd64`).
- A populated `.env` (referenced by the prod compose services).

## After the push: host pull is required

Pushing to ECR does **not** restart prod. On the EC2 host:

```bash
cd ring
git checkout dev            # detached HEAD makes `git pull` fail
git pull origin dev
./dev_util/prod.sh
ring compose any --profile prod up -d --force-recreate --remove-orphans
```

`--remove-orphans` clears containers whose services were removed from the
compose files (e.g. the retired `ring-frontend` container).

The API volume-mounts `./ring` with `--reload`, so the checkout on disk is the
running Python. Verify with:

```bash
curl -sS https://ring.neilsriv.tech/api/v1/version
```

Expect a 200 JSON body with `git.sha`, `image_build.sha`, and
`docker.containers[].image_id` / `image_digest`. Container identity comes
from `.ring-runtime-version.json` written by `ring compose` / `prod.sh` —
the API does not mount `docker.sock`. A connection error or missing route
means the host is still on a pre-version image/checkout.

Do not skip `--force-recreate`: compose keeps the old container when the local
tag name (`prod-ring-api:latest`) is unchanged.

## Frontend deploys (for reference)

- Merge to `dev` → Cloudflare Workers Builds builds `react/` and deploys
  the `ring-frontend` Worker (~2 min). No ECR, no EC2 involvement.
- Maintenance mode: set `VITE_MAINTENANCE_MODE=true` in the Worker's
  build variables (Settings → Build) and retry the latest build; unset
  to restore.
- Rollback: redeploy a previous version from the Worker's Deployments
  tab in the Cloudflare dashboard.

## Notes

- Pushing publishes `:latest`; there is no per-release version tag today.
- Image/registry names live in `dev_util/docker.py`; the deploy command lives in
  `dev_util/deploy.py`.
- Builds bake the current git SHA into image labels (`org.opencontainers.image.revision`)
  and `RING_BUILD_GIT_*` env vars via `dev_util/git_meta.py`.
