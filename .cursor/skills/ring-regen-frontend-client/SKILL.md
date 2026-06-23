---
name: ring-regen-frontend-client
description: Regenerate the Ring frontend's `@hey-api` client and TanStack Query hooks from the live FastAPI OpenAPI spec. Use after backend API changes, when adding a new endpoint to the React app, or when the user sees 404s, missing SDK functions, or TypeScript errors in `react/src/client/`.
---

# Regenerating the Ring frontend client

The frontend never hand-writes API calls. The SDK in `react/src/client/`
(`sdk.gen.ts`, `types.gen.ts`, `client.gen.ts`, and TanStack Query hooks under
`@tanstack/`) is generated from the backend's OpenAPI spec by
`@hey-api/openapi-ts`.

## When to run this

- Added or changed a FastAPI route, request body, or response schema.
- Renamed or removed an endpoint.
- The frontend suddenly has TypeScript errors referencing missing SDK
  functions or types.
- The frontend gets `404`s for endpoints that exist on the backend.

## Workflow

```
Task progress:
- [ ] API container is running
- [ ] Run `ring fe regen`
- [ ] Spot-check `react/src/client/sdk.gen.ts`
- [ ] Update callers / wire TanStack Query hooks
- [ ] Run `npx tsc --noEmit`
```

### 1. Ensure the API is up

`ring fe regen` (see [dev_util/frontend.py](../../../dev_util/frontend.py))
curls `http://localhost:8001/api/v1/openapi.json` from the host. The API
container must be running:

```bash
ring compose up
ring compose ps  # confirm `api` is healthy
```

In the Cursor Cloud VM, use the raw compose form documented in
[AGENTS.md](../../../AGENTS.md#cursor-cloud-agent-vm).

### 2. Regenerate

```bash
ring fe regen
```

This runs three steps under the hood:

1. `curl http://localhost:8001/api/v1/openapi.json` → writes
   `react/openapi.json`.
2. `node modify-openapi-operationids.js` → normalizes operation IDs so the
   generated SDK has stable function names.
3. `pnpm run generate-client` → invokes `openapi-ts` with
   [react/openapi-ts.config.ts](../../../react/openapi-ts.config.ts), which uses
   the `@hey-api/client-axios` and `@tanstack/react-query` plugins.

### 3. Verify

- Open `react/src/client/sdk.gen.ts` and confirm the new/renamed function is
  present.
- Look at `react/src/client/@tanstack/` for the generated query/mutation
  options.
- Run:

  ```bash
  cd react && npx tsc --noEmit
  ```

### 4. Use the generated hooks

In components, prefer the generated TanStack Query options over calling the
SDK directly:

```tsx
import { useQuery, useMutation } from "@tanstack/react-query"
import { someResourceOptions, createSomeResourceMutation } from "@/client/@tanstack/react-query.gen"

const { data } = useQuery(someResourceOptions({ path: { id } }))
const mutate = useMutation(createSomeResourceMutation())
```

## Troubleshooting

- **`curl: (7) Failed to connect`** — the API isn't running on `:8001`. Start
  it with `ring compose up` (or the sudo compose form in the Cloud VM).
- **Generated file looks unchanged** — the spec endpoint returned stale data;
  rebuild the API container (`ring compose any build api` then restart).
- **TS errors after regen** — the regenerated names changed; update callers
  rather than reverting the generated file.
