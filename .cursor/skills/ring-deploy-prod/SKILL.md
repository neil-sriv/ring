---
name: ring-deploy-prod
description: Build and ship Ring's production images to public ECR. Use when the user asks to deploy to prod, push prod images, release, or rebuild/publish the frontend, api, or llm images to public.ecr.aws.
---

# Deploying Ring to prod

Prod runs from images published to the public ECR registry
`public.ecr.aws/z2k1e8p1/` (`ring-frontend`, `ring-api`, `ring-llm`). Deploying
means building those images locally, authenticating to ECR, and pushing them.

## One command

```bash
ring deploy prod
```

This runs, in order:

1. `ring fe build` — build the frontend bundle (`react/dist`) served by nginx.
2. `compose --profile prod build` — build all prod images, passing
   `VITE_API_URL` / `VITE_MAINTENANCE_MODE` as frontend build args.
3. `aws ecr-public get-login-password | docker login … public.ecr.aws` —
   authenticate Docker against public ECR (`us-east-1`).
4. `ring docker tp` — tag the `prod-*` images and push them to ECR.

### Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--vite-api-url` | `https://ring.neilsriv.tech` | `VITE_API_URL` baked into the frontend image |
| `--maintenance-mode` / `--no-maintenance-mode` | off | `VITE_MAINTENANCE_MODE` build arg |
| `--region` | `us-east-1` | AWS region for the ECR login |
| `--skip-fe-build` | off | Reuse existing `react/dist`, skip step 1 |
| `--skip-login` | off | Skip step 3 if already logged in |

## Manual equivalent

```bash
uv run ring fe build
VITE_API_URL=https://ring.neilsriv.tech VITE_MAINTENANCE_MODE=false \
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
ring compose any --profile prod up -d --force-recreate
```

The API volume-mounts `./ring` with `--reload`, so the checkout on disk is the
running Python. Verify with:

```bash
curl -sS https://ring.neilsriv.tech/api/v1/version
```

Expect a 200 JSON body with `git.sha`, `image_build.sha`, and
`docker.containers[].image_id` / `image_digest`. A connection error or missing
route means the host is still on a pre-version image/checkout.

Do not skip `--force-recreate`: compose keeps the old container when the local
tag name (`prod-ring-api:latest`) is unchanged.

## Notes

- Pushing publishes `:latest`; there is no per-release version tag today.
- Set `--maintenance-mode` to ship a frontend that renders the maintenance page.
- Image/registry names live in `dev_util/docker.py`; the deploy command lives in
  `dev_util/deploy.py`.
- Builds bake the current git SHA into image labels (`org.opencontainers.image.revision`)
  and `RING_BUILD_GIT_*` env vars via `dev_util/git_meta.py`.
