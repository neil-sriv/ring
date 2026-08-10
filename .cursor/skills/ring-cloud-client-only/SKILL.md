---
name: ring-cloud-client-only
description: Run Ring's local Vite frontend against the production API from the Cursor Cloud Agent environment "Ring client only". Use for frontend-only work, production-data UI checks, or configuring the client-only saved environment.
---

# Ring Client Only

Use the Cursor saved environment **Ring client only** for frontend work against
the deployed Ring API.

```
Browser → Vite (:5173) → same-origin /api/v1 proxy
        → https://ring.neilsriv.tech → prod API → prod DB
```

The frontend never receives a database URI. No local API, Cockroach container,
CA certificate, scheduler override, or production database credentials are
needed.

## Environment setup

Create **Ring client only** as a saved environment in the
[Cloud Agents dashboard](https://cursor.com/dashboard/cloud-agents#environments)
and select it explicitly when launching frontend-only work. Keep the committed
[`.cursor/environment.json`](../../../.cursor/environment.json) as the default
**Ring full stack** environment.

Suggested dashboard configuration:

**Install**

```bash
uv sync --group dev && (cd react && pnpm install)
```

**Start**

Leave empty. Do not put `ring cloud client-only check` here — a failed
reachability check would block environment boot, and **Terminal**’s `dev`
already runs the same check by default.

**Terminal**

```bash
ring cloud client-only dev
```

If the Cloud VM cannot reach `ring.neilsriv.tech` yet (for example
`ECONNRESET` before egress/allow-all applies), use:

```bash
ring cloud client-only dev --skip-check
```

The environment does not need Docker startup. `uv sync` installs the shared
`ring` CLI into `.venv/bin`; Cloud Agent shells include it on `PATH`.

## Secrets

No database secrets are needed. Do not add any Cockroach URI or CA certificate
to this environment.

If automated browser login is desired, add a dedicated production test account
as runtime secrets. Otherwise log in manually with an existing account.

## Commands

```bash
ring cloud client-only check
ring cloud client-only dev
ring cloud client-only dev --skip-check
```

`check` verifies the deployed OpenAPI endpoint is reachable (manual / optional;
not a dashboard Start command). `dev`:

1. verifies the production API (unless `--skip-check`);
2. sets `VITE_API_URL` empty so browser requests remain same-origin;
3. sets `VITE_API_PROXY_TARGET=https://ring.neilsriv.tech`;
4. starts Vite on `0.0.0.0:5173`.

Use `--skip-check` when you need Vite up even though the prod health check
fails; the proxy target is still set, so API calls succeed once egress works.

Override the target or port only when explicitly needed:

```bash
ring cloud client-only dev --api-url https://ring.neilsriv.tech --port 5173
```

## Why proxy instead of `VITE_API_URL`?

Setting `VITE_API_URL=https://ring.neilsriv.tech` makes the browser issue
cross-origin requests and requires production CORS changes. Keeping
`VITE_API_URL` empty makes the browser call the Vite origin; Vite forwards HTTP
and WebSocket traffic to production server-side.

Nginx is not involved in the client-only environment. Vite provides the
development proxy.

## Safety

- Requests can mutate live production data through the deployed API.
- Use normal API authorization; never give the frontend or agent direct DB
  credentials.
- Do not run local backend migrations or bootstrap Docker in this environment.
- Use **Ring full stack** for backend changes and local-data testing.

## Browser check

1. Open http://localhost:5173/login.
2. Log in with a production account.
3. Confirm groups and letters load through `/api/v1`.
4. For notebook work, confirm WebSockets connect through the same Vite proxy.

## Related

- Full-stack bootstrap: [ring-cloud-dev](../ring-cloud-dev/SKILL.md)
- Production topology: [docs/infrastructure.md](../../../docs/infrastructure.md)
