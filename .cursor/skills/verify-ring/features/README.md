# Ring verification map

This directory is the maintained source for verifying Ring's user-facing
behavior. Read the index, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch with `bash .cursor/skills/verify-ring/scripts/launch.sh` and wait for
  `=== verify-ring ready ===`.
- App URL is `http://localhost:5173`. API URL is `https://localhost/api/v1/`
  through `scripts/api.sh`.
- Seeded user: `test@example.com` / `testpassword123` (name `Test User`).
- Run `bash .cursor/skills/verify-ring/scripts/doctor.sh` and require the
  version SHA to match `git rev-parse HEAD`.
- Read `RUN_ID` from `/tmp/verify-ring/state.env`. Put it in names and emails
  created during the run so a later run does not collide with unique group
  names or emails.
- Never drive an instance that this verification run did not health-check.
- Do not point the stack at CockroachDB Cloud.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say
  otherwise.
- Prefer ARIA roles and accessible names over CSS selectors or DOM position.
- UI actions go through the browser at `http://localhost:5173`.
- API actions go through `bash .cursor/skills/verify-ring/scripts/api.sh`.
- Row checks go through `bash .cursor/skills/verify-ring/scripts/db-query.sh`.
- Quote the SQL identifiers `"user"` and `"group"`.
- Keep JWTs in `/tmp/verify-ring/` mode `0600`. Do not copy them into evidence.
- Leave proof artifacts in `/opt/cursor/artifacts/verify-ring/<run-id>/`.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof includes a screenshot with the page heading or the Ring wordmark.
- API proof includes the HTTP status and the response body with secrets
  removed.
- Mutation proof includes a read-only SQL view of the stored row after a
  reload or a second request.
- Record the feature id and the entry point used with every artifact.
- Report an unreachable path with the attempted step and the unmet
  precondition. Do not report a skipped entry point as verified through a
  different path.

## Feature entry contract

Each feature file starts with an H1 and one paragraph, then these H2 sections
in order: `Sub-features`, `How to get to it (user POV)`, `Driving it`,
`Gotchas`.

## Features

- [Sign in](./auth-login.md) covers the login form, a bad password, logout,
  and the nginx token endpoint.
- [Create a group](./groups-create.md) covers every create-group button and a
  second user denied by the authz helpers.
- [Respond to a letter](./letter-respond.md) covers starting a loop, opening
  it for replies, and saving an answer that survives a reload.
