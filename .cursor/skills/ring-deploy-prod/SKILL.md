---
name: ring-deploy-prod
description: Build and ship Ring's production images to public ECR, or roll them out on the EC2 host. Use when the user asks to deploy to prod, push prod images, release, run CD, or rebuild/publish the frontend, api, or llm images to public.ecr.aws.
---

# Deploying Ring to prod

Prod runs from images published to the public ECR registry
`public.ecr.aws/z2k1e8p1/` (`ring-frontend`, `ring-api`, `ring-llm`). Deploying
means building those images, pushing them, then pulling/restarting Compose on
the EC2 host.

## Preferred: GitHub Actions CD

Trigger **Actions → Deploy Prod → Run workflow**
([`.github/workflows/deploy_prod.yml`](../../../.github/workflows/deploy_prod.yml)):

1. Build/push images to ECR (`:latest` + `:<git-sha>`).
2. SSH to EC2 and run `./dev_util/deploy_host.sh --ref <sha>`.

Inputs: `maintenance_mode`, `deploy_host`, `include_llm`, `skip_migrate`.

Required secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `PROD_SSH_HOST`,
`PROD_SSH_USER`, `PROD_SSH_KEY`. Variables: `PROD_APP_DIR`, `PROD_SSH_PORT`.

## Local one command (push only)

```bash
ring deploy prod
```

This runs, in order:

1. `ring fe build` — build the frontend bundle (`react/dist`) served by nginx
   (skip with `--skip-fe-build`; the frontend image builds its own dist).
2. `compose --profile prod build` — build selected prod images, passing
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
| `-i` / `--image` | all three | Limit which images to build/push |
| `-t` / `--extra-tag` | none | Also push this tag (e.g. git SHA) |

## Host rollout

On the EC2 host (or via CD SSH):

```bash
./dev_util/deploy_host.sh
# or:
ring deploy host --ref <sha> -i ring-api -i ring-frontend
```

This syncs git (optional `--ref`), pulls/retags ECR images, copies
`react/dist` out of `prod-ring-frontend` for nginx's SW/manifest mounts, runs
`ring db upgrade`, then `compose up -d` + nginx restart.

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
- A populated `.env` on the **host** (referenced by the prod compose services).
  CI only needs a stub `.env` for compose build.

## Notes

- Pushing always publishes `:latest`; CD also publishes `:<git-sha>`.
- Set `--maintenance-mode` to ship a frontend that renders the maintenance page.
- Image/registry names live in `dev_util/docker.py`; the deploy command lives in
  `dev_util/deploy.py`.
