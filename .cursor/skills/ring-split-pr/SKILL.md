---
name: ring-split-pr
description: Split a Ring change that touches both the FastAPI backend and the React frontend into two stacked, independently reviewable PRs (backend first, then frontend). Use when a single feature adds or modifies an API endpoint and its corresponding UI, when the diff is large, or when the user asks to split work into separate PRs.
---

# Splitting Ring work into backend + frontend PRs

Ring's backend (`ring/`) and frontend (`react/`) are reviewed independently.
For anything bigger than a trivial change, land the backend first so the
OpenAPI surface is stable, then land the frontend on top of the regenerated
client. This keeps each PR small and lets reviewers focus.

## When to split

- The change adds, renames, or removes an API endpoint.
- A new model or migration is involved.
- The frontend change is large enough that a reviewer would want to look at
  it without scrolling through backend diffs.
- The user explicitly asks for a stacked / split PR.

For tiny tweaks (e.g. fixing a label, changing a CSS class, adjusting a
default value in a schema with no UI impact) a single PR is fine.

## Workflow

```
Task progress:
- [ ] PR 1 (backend) branch from main
- [ ] Land models/migration/API/tests/OpenAPI
- [ ] CI green on PR 1 (lint, tests)
- [ ] PR 2 (frontend) branch from PR 1
- [ ] ring fe regen + UI changes
- [ ] CI green on PR 2 (lint, tsc, build)
- [ ] After PR 1 merges, rebase PR 2 onto main
```

### PR 1 — backend

Scope:

- New/changed models, schemas, CRUD, FastAPI routes
- Alembic migration
- Authz policy/code updates (see `ring-authz-checklist`)
- Backend unit tests
- The `react/openapi.json` and **regenerated** `react/src/client/` if the API
  surface changed — committing the regenerated client here keeps the
  frontend buildable on `main` between PRs

Quality gates that must pass:

```bash
ring check lint
ring test run
cd react && npx tsc --noEmit   # ensures committed client matches OpenAPI
```

Branch name (per personal preference): `neil/<short-slug>-backend`.

### PR 2 — frontend

Branch from the PR 1 branch (jj):

```bash
jj new <pr1-change-id>
# Title with neil/<short-slug>-frontend bookmark when ready
```

Scope:

- UI components, routes, hooks under `react/src/`
- Any non-generated changes to `react/src/client/` wrappers
- Frontend tests / Storybook (if applicable)

Quality gates:

```bash
cd react && pnpm run lint
cd react && npx tsc --noEmit
cd react && pnpm run build
```

After PR 1 merges, rebase PR 2 onto `main`:

```bash
jj rebase -s <pr2-change> -d main@origin
```

## When the split isn't worth it

If the API change is purely additive and trivial (e.g. one new optional query
param), it's fine to ship backend + frontend in one PR — just make sure
`ring fe regen` was run and the regenerated client is committed in the same PR.

## See also

- `ring-add-backend-resource` — what to put in PR 1
- `ring-regen-frontend-client` — the regen step between the two PRs
- `ring-authz-checklist` — usually belongs in PR 1
