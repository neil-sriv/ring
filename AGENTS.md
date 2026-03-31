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
## Learned User Preferences
- When extending session authentication, prefer refresh tokens so users are not forced to log in again when the access token expires.
- Prefer JWT refresh-token rotation and refresh/access token type validation for better security.
- For comment-like entities that can attach to arbitrary objects, prefer a generic weak-reference design that stores only the target object's `api_identifier` (not a hard foreign key).
- Prefer hard deletes over soft deletion fields for the comment model.
- Prefer using the comment API prefix `cmnt`.
- For large, multi-surface changes, prefer splitting work into multiple PRs (backend first, then frontend) rather than one large PR.
- For operational resilience (timeouts), prefer existing/popular timeout mechanisms or FastAPI-provided solutions over custom timeout middleware.

## Learned Workspace Facts
- The system is intended to use short-lived JWT access tokens (~15 minutes) and longer-lived refresh tokens (~30 days) with refresh/access token type validation and rotation.
- The frontend is expected to auto-refresh access tokens on `401` using the stored refresh token and to clear both tokens on logout.
- Image upload handling should have timeouts configured to avoid long hangs (nginx proxy timeouts for `/api/v1/` and botocore/boto3 S3 client timeouts for uploads/downloads).
- The comment model is intended to be generic, attaching to targets via `target_api_id` (storing the target's `api_identifier`) and using `cmnt` as the comment API prefix, without soft deletion.
