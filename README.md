# Ring

This is a clone of LetterLoop as a fun side project.

## Set up

### Requirements

- Orbstack or Docker Installed
- node v18 or greater
- pnpm

### First Time Dev Setup

#### uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
```

There is a `pyproject.toml` file that will install local `ring` commands and requirements.

```bash
uv sync --group dev --group ai
```

### `env` set up

There are a few setup steps to get the project running locally. Make sure you are in a virtual environment:

```bash
source .venv/bin/activate
```

Then:

```bash
docker network create ring-network
```

At this point:

```bash
rm -rf localhost.key localhost.crt
ring setup local-ssl
chmod 600 certs/node.key
```

Add a `.env` file with the following:

```bash
ENVIRONMENT=local
API_PORT=8001
SQLALCHEMY_DATABASE_URI=postgresql://ring-postgres:ring-postgres@db:5432/ring
COCKROACH_DATABASE_URI=cockroachdb://ringcockroach:ringcockroach@cockroach:26257/ring?sslmode=require
JWT_SIGNING_ALGORITHM=HS256
VITE_API_URL=https://localhost
BACKEND_CORS_ORIGINS="https://localhost:5173 http://localhost:5173"
SW_DEV=true
VITE_MAINTENANCE_MODE=false
```

We'll need to generate `JWT_SIGNING_KEY`, `LLM_SERVICE_API_KEY`, and `VAPID_PRIVATE_KEY` using `openssl`:

```bash
echo "JWT_SIGNING_KEY=$(openssl rand -hex 32)" >> .env
echo "LLM_SERVICE_API_KEY=$(openssl rand -hex 32)" >> .env
echo "VAPID_PRIVATE_KEY=$(openssl rand -hex 32)" >> .env
```

Now you should be able to get FastAPI going:

```bash
ring compose up
ring compose ps  # to verify everything is running
```

You can visit `https://localhost/api/v1/docs` to get to the swagger documentation!

### Frontend Setup

Install frontend dependencies:

```bash
ring fe install
```

### Backend Setup

Initialize the database (tables will be empty):

```bash
ring db upgrade
```

## Development

### Running the server

```bash
ring compose up
```

API accessible and `localhost/api/v1/docs`

### Running the client

```bash
ring fe dev
```

Accessible at http://localhost:5173 during Vite dev. The dev server proxies
`/api/v1` to the API on port 8001, so `VITE_API_URL` can be left empty in
`.env` (see `.env.cloud.example`). Production builds still use
`VITE_API_URL=https://localhost` to reach nginx.

### Cursor Cloud Agent

Cloud VMs use [`.cursor/environment.json`](.cursor/environment.json): `install`
pulls deps, `start` runs `bash .cursor/cloud-start.sh --bootstrap-only`, and a
`vite` terminal runs the frontend.

```bash
bash .cursor/cloud-start.sh              # bootstrap + Vite (manual)
bash dev_util/cloud-health.sh            # verify stack
```

| | URL |
|---|---|
| App | http://localhost:5173 |
| API docs | http://localhost:8001/api/v1/docs |
| Test login | `test@example.com` / `testpassword123` |

Agent playbook: [`.cursor/skills/ring-cloud-dev/SKILL.md`](.cursor/skills/ring-cloud-dev/SKILL.md).
Copy [`.env.cloud.example`](.env.cloud.example) to `.env` if bootstrap has not
run yet.

To use CockroachDB Cloud data from the local Vite frontend, see
[`.cursor/skills/ring-cloud-prod-db/SKILL.md`](.cursor/skills/ring-cloud-prod-db/SKILL.md)
(`ring cloud prod-db enable`).

### `ring` commands

#### `ring cloud`

Cursor Cloud Agent helpers:

```bash
ring cloud prod-db status
ring cloud prod-db enable --staging --yes
ring cloud prod-db disable
ring cloud prod-db health
```

#### `ring compose`

Docker Compose wrapper for managing services. By default uses `compose.dev.yml`, use `--profile prod` for production.

```bash
ring compose up      # Start services
ring compose ps      # Check service status
ring compose any     # Run any docker compose command
```

#### `ring db`

Database management commands:

```bash
ring db upgrade     # Run database migrations
ring db generate    # Generate new migration
ring db cockroach   # Open CockroachDB SQL shell
ring db alembic     # Run alembic commands directly
```

#### `ring docker`

Docker registry management:

```bash
ring docker push    # Push images to registry
ring docker tag     # Tag images
ring docker tp      # Tag and push
```

#### `ring fe`

Frontend development commands:

```bash
ring fe install     # Install frontend dependencies
ring fe dev         # Start development server
ring fe build       # Build for production
ring fe regen       # Regenerate API client
```

#### `ring run`

Utility commands:

```bash
ring run script     # Run a script
ring run shell      # Start a shell
```

## Deployment

Prod runs Docker Compose on a single EC2 instance. Images are stored in **ECR
Public** (`public.ecr.aws/z2k1e8p1/`); the database is **CockroachDB Cloud**
(`ring-db`). See [docs/infrastructure.md](docs/infrastructure.md) for the full
topology (S3, CloudFront, SES, request flows).

### Deploy the frontend

Nothing to run: Cloudflare Workers Builds redeploys the frontend on every
push to `dev`, live about a minute later. Watch the **Workers Builds:
ring-frontend** check on the commit.

### Publish API images

Pushes to `dev` that touch backend paths publish `ring-api:latest` and
`ring-api:<sha>` to ECR Public (Actions → **Publish ring-api**). Frontend
prod is Cloudflare Workers; do not build `ring-frontend` unless you are
rolling back to the nginx SPA.

`ring deploy prod` defaults to `ring-llm` (still manual). Day-to-day
`ring-api` publishes via CI; laptop API builds confirm first:

```bash
ring deploy prod -i ring-llm
ring deploy prod -i ring-api -t "$(git rev-parse HEAD)"   # break-glass; confirms
```

### Deploy on the host

Automatic: a backend merge to `dev` publishes an image, and a successful
publish runs **Deploy ring-api** — backend tests, migration check, then SSH
to EC2 and `deploy_host.sh --rollback-on-fail`. The `prod-deploy`
concurrency group queues runs so two deploys cannot race migrations.

The same workflow is a `workflow_dispatch` button (optional SHA input) for
manual deploys and rollbacks.

To freeze automatic deploys during an incident, set the repo variable
`DEPLOY_PAUSED=true`. Manual runs still work, so rollback stays available.

Needs repo secrets `PROD_SSH_HOST` (EC2 public IP or gray-cloud DNS —
Cloudflare will not forward SSH on the orange `ring.neilsriv.tech`),
`PROD_SSH_USER`, `PROD_SSH_KEY` (dedicated deploy key, not a laptop key).
Optional repo variables: `PROD_SSH_PORT` (22), `PROD_APP_DIR`
(`$HOME/ring`).

Or SSH in yourself:

```bash
cd ring
./dev_util/deploy_host.sh <published-sha>  # pin / rollback
# uv run ring deploy host <sha>            # same script
```

That syncs git (compose/nginx), pulls `ring-api:<sha>`, runs
`uv run ring db upgrade --profile prod`, recreates Compose, and checks
`GET /api/v1/version` (`image_build.sha`). Prod runs the image
filesystem — pass a SHA that `publish_api.yml` actually tagged, not a
docs-only `HEAD`. To roll back an image without reverting compose to a
pre-cutover commit: `./dev_util/deploy_host.sh --skip-git <sha>`.

### See what is live

```bash
ring deploy status
# frontend   d615e40  dev  deployed 3m ago    up to date with origin/dev  via workers_ci
# api        195c464  dev  committed 8h ago   1 commit behind origin/dev  via image_env
```

Frontend and API report themselves at `/version.json` and
`/api/v1/version`; the app shows the same thing under
**Settings → Build**.
