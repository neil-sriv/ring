---
name: verify-ring
description: Drive the Ring web app the way a user does — login, groups, and letter responses — against the local Vite and nginx stack, and capture screenshots plus database rows. Use before marking a behavior-changing PR ready, or whenever a change needs proof on the running app.
---

# Verify Ring

Ring's user-facing surface is the React app at `http://localhost:5173`. The API
for verification is nginx at `https://localhost/api/v1/` (self-signed cert).
Direct `:8001` is for tooling only. This skill drives that stack. It does not
target CockroachDB Cloud.

Ports `5173`, `4173`, `8001`, `443`, and `26257` are fixed, and Cockroach data
is one Docker volume. Do not start a second stack. If `launch.sh` reports an
active run, stop or finish that run before launching again.

Feature recipes live in [features/README.md](features/README.md). Read the
index, then follow the feature file. Do not report a skipped entry point as
verified through a different path.

## Launch

From the repo root:

```bash
bash .cursor/skills/verify-ring/scripts/launch.sh
```

What that script does:

1. Refuses to run when `.ring-cloud-prod-db/mode` exists. Bootstrap runs
   `alembic upgrade head` against the database in `.env`.
2. Starts the Docker daemon with `sudo service docker start` when `docker info`
   fails. The cloud environment start hook does the same thing;
   [`.cursor/cloud-start.sh`](../../../.cursor/cloud-start.sh) assumes the
   daemon is already up.
3. Runs `bash .cursor/cloud-start.sh --bootstrap-only`. That creates the
   network, brings up Compose, waits for Cockroach, enables the vector index,
   runs migrations, waits for the API, and seeds `test@example.com` /
   `testpassword123` via [`dev_util/cloud-seed.sh`](../../../dev_util/cloud-seed.sh).
4. Starts the Vite dev server with `bash .cursor/cloud-start.sh --vite-only`
   in tmux session `verify-ring-vite` when nothing is already serving
   `:5173`. That script forces `VITE_API_URL=""` and `SW_DEV=false`.

**Ready** is the line `=== verify-ring ready ===`. That is printed only after
all of the following are true:

- `bash dev_util/cloud-health.sh` passes (Cockroach, API `:8001`, Vite
  `:5173`, nginx `:443`).
- `curl -sf http://localhost:5173/src/main.tsx` contains `createRoot`.
- `POST https://localhost/api/v1/login/access-token` for the seeded user
  returns a bearer token.

The `=== Ring cloud ready ===` banner from `--bootstrap-only` is earlier.
Vite is not up yet at that banner, so the app is not usable.

The run id and evidence directory are printed at ready and stored in
`/tmp/verify-ring/state.env`. Evidence goes to
`/opt/cursor/artifacts/verify-ring/<run-id>/`.

If launch fails after it has started Compose or Vite, run cleanup before
retrying.

## Doctor

```bash
bash .cursor/skills/verify-ring/scripts/doctor.sh
```

Read-only. Run it before the first drive, and again after anything surprising
(a failed login, a 500, a wedged page). It:

- runs `bash dev_util/cloud-health.sh`
- `GET /version` through nginx and requires `git.sha` to equal
  `git rev-parse HEAD` (retries for the 15s cache in
  `ring/lib/version_info.py`; a dirty worktree is fine)
- confirms the seeded user still receives a bearer token, without printing it
- when this run started Vite, checks that pane pid is alive

A doctor failure means do not drive. Fix the instance (relaunch) or, when the
check itself drifted, fix this skill and retry once.

## Drive

UI drives use a browser at `http://localhost:5173`. Prefer the accessible
names in the feature files (`role` + name from the visible label). Do not
drive `https://localhost/` for UI steps: nginx serves `react/dist` there and
SPA routes 404 until a build exists.

API drives use the helper, which calls nginx with `-k`:

```bash
bash .cursor/skills/verify-ring/scripts/api.sh GET /version
bash .cursor/skills/verify-ring/scripts/api.sh POST /login/access-token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=test@example.com&password=testpassword123'
```

Login is form-encoded (`username`, `password`), matching
`OAuth2PasswordRequestForm` on `POST /login/access-token`. Store tokens under
`/tmp/verify-ring/` with mode `0600`. Do not copy JWTs into the evidence
directory or a PR.

Database checks:

```bash
bash .cursor/skills/verify-ring/scripts/db-query.sh \
  "SELECT api_identifier, email FROM \"user\" WHERE email = 'test@example.com'"
```

`group` and `user` are reserved table names; quote them.

Run `doctor.sh` before the first feature. Then follow that feature's
**Driving it** section literally, including every entry point it lists.

### Preview

`pnpm run build` has shipped a blank page when the bundle evaluated a circular
chunk before React initialized. Confirm the built app in a browser.

```bash
bash .cursor/skills/verify-ring/scripts/preview.sh
```

The script builds `react/` with `VITE_API_URL=""` and `SW_DEV=false`
(`pnpm run build`, which is `tsc && vite build`). If `react/dist` exists but
is not writable (nginx's bind mount creates it as root on a fresh checkout),
the script runs `sudo chown` on that directory before the build. It then serves
`pnpm exec vite preview --host 127.0.0.1 --port 4173 --strictPort` in tmux
session `verify-ring-preview`.

Open `http://127.0.0.1:4173/login` in a browser. Pass only when all of these
are true:

- heading `Welcome back` is visible
- a button named `Sign In` is visible
- the Ring wordmark is visible
- `#root` has element children
- there is no full-page error overlay

Save a screenshot to `$EVIDENCE_DIR/preview/login.png`. A `curl` of the HTML
shell is not this check: the blank-page failure still returns `index.html`
with an empty root. `vite preview` does not proxy `/api/v1` (the proxy is
only on the Vite dev server). A failed login on `:4173` is not a blank page.

## Evidence

Write proof under the evidence directory launch printed
(`/opt/cursor/artifacts/verify-ring/<run-id>/`). One subdirectory per
feature, plus `preview/` for the blank-page check. Cleanup must leave this
tree in place.

For each drive, capture:

- the user action and the resulting screen, not only the final screen
- a screenshot that shows the Ring wordmark or the page heading
- the feature id and which entry point was used
- side effects in Cockroach via `db-query.sh`, not only HTTP 200

A toast (`Success!` / `Group created successfully.`) is not proof. Reload the
page or open the record again, and read the row back. Do not use test-only
endpoints or direct ORM writes. Mocks are out of scope; Spotify staying
unconfigured is a real boundary, and the groups recipe treats the post-authz
Spotify status as the member's result.

Do not put JWTs, passwords, or `hashed_password` in evidence files.

## Cleanup

```bash
bash .cursor/skills/verify-ring/scripts/cleanup.sh
```

Stops only what this run recorded in `/tmp/verify-ring/state.env`:

- tmux session `verify-ring-vite`, when launch started Vite
- tmux session `verify-ring-preview`, when preview was started
- `sudo docker compose -f compose.core.yml -f compose.dev.yml --profile dev down`,
  when launch started Compose

It does not `docker compose down -v`, does not kill by process name, and does
not delete evidence. After it exits, the evidence directory must still exist.
A second cleanup with no state file is a no-op.

Run cleanup after a failed launch too, so a half-started stack is not left
behind. Then confirm the evidence directory is still there.

## Helpers

| Script | Invocation |
| --- | --- |
| `scripts/lib.sh` | `source .cursor/skills/verify-ring/scripts/lib.sh` (not a command) |
| `scripts/launch.sh` | `bash .cursor/skills/verify-ring/scripts/launch.sh` |
| `scripts/doctor.sh` | `bash .cursor/skills/verify-ring/scripts/doctor.sh` |
| `scripts/api.sh` | `bash .cursor/skills/verify-ring/scripts/api.sh METHOD /path [curl args...]` |
| `scripts/db-query.sh` | `bash .cursor/skills/verify-ring/scripts/db-query.sh "SELECT ..."` |
| `scripts/preview.sh` | `bash .cursor/skills/verify-ring/scripts/preview.sh` |
| `scripts/cleanup.sh` | `bash .cursor/skills/verify-ring/scripts/cleanup.sh` |

Each script prints its usage when arguments are missing. Paths above are from
the repo root.

## Maintenance

When the app changes, re-check this map with `/maintain-verification-skill`.
A behavior the map describes that the app no longer does is either doc drift
or a product bug. Fix drift in this skill. Report product bugs; do not weaken
a journey so the run goes green.
