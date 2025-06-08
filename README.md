# Ring

This is a clone of LetterLoop as a fun side project.

## Set up

### Requirements

- Orbstack or Docker Installed
- node v18 or greater
- pnpm
- oh-my-zsh (recommended)

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
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
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

### `oh-my-zsh` set up

**Highly** recommend to use `oh-my-zsh` with the `virtualenvwrapper` and `dotenv` plugins.

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

Accessible at `https://localhost:5173`

### `ring` commands

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
ring db pgcli       # Open database CLI
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

### Build new images

```bash
VITE_API_URL=http://ring.neilsriv.tech ring compose any --prod build
```

### Push to registry

```bash
ring docker tp
```

### Deploy

- ssh into the server

```bash
cd ring
git pull
./dev_util/prod.sh
ring db upgrade
ring compose any --prod up -d
# may need to restart nginx
ring compose any --prod restart nginx
```
