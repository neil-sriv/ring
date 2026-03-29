# AGENTS.md

## Cursor Cloud specific instructions

### Architecture overview

Ring is a collaborative letter/newsletter platform (LetterLoop clone) with three main components:

| Component | Tech | Port |
|-----------|------|------|
| **Backend API** | FastAPI + SQLAlchemy + CockroachDB | 8001 (via Docker) |
| **Frontend** | React + Vite + ChakraUI + TanStack | 5173 (Vite dev server) |
| **Nginx** | Reverse proxy for API + SSL | 443/80 (via Docker) |
| **CockroachDB** | Database (PostgreSQL-compatible) | 26257 (via Docker) |

The `ring` CLI (installed via `uv sync`) provides dev workflow commands — see `README.md` for the full list.

### Starting services

All backend services run via Docker Compose. The `ring` CLI wraps docker compose commands:

```bash
# Activate venv first
source .venv/bin/activate

# Start CockroachDB + API + Nginx
sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev up --build --detach

# Run database migrations (runs inside the API container)
sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev exec -w /src/ring api alembic upgrade head

# Start frontend dev server
cd react && pnpm run dev
```

**Gotcha:** CockroachDB requires vector indexes to be enabled before migrations will succeed. Run this once after the CockroachDB container first starts:
```bash
sudo docker exec ring-cockroach ./cockroach sql --certs-dir=/root/.cockroach-certs -d ring -e "SET CLUSTER SETTING feature.vector_index.enabled = true;"
```

### Lint, test, build

- **Python lint:** `uv run ruff format --diff && uv run ruff check`
- **Frontend lint:** `cd react && pnpm run lint` (uses Biome with `--apply-unsafe`; ~21 pre-existing security warnings are expected)
- **TypeScript check:** `cd react && npx tsc --noEmit`
- **Backend tests:** Run via Docker using `compose.test.yml`:
  ```bash
  sudo docker compose -f compose.test.yml --profile test up --build --detach
  sudo docker logs -f ring-test-runner
  ```
  Tests use a separate CockroachDB instance on port 8008. 242/243 tests pass; 1 pre-existing `IntegrityError` in `TestGroupApi::test_list_groups`.
- **Frontend build:** `cd react && pnpm run build`

### Important notes

- The `.env` file is required at the repo root with keys documented in `README.md`. It is `.gitignore`d.
- SSL certificates are generated via `bash dev_util/ssl.sh` and stored in `localhost.crt`, `localhost.key` (for Nginx) and `certs/` (for CockroachDB). Cert `certs/node.key` must have `chmod 600`.
- Docker commands require `sudo` in the Cloud Agent VM.
- The frontend Vite dev server at `https://localhost:5173` communicates with the backend through the Nginx reverse proxy at `https://localhost/api/v1/`.
- The LLM microservice (`llm/`) is optional and requires additional setup (Ollama or Gemini/OpenAI API keys).
