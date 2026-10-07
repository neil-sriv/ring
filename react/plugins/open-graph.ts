/**
 * Serve the same Open Graph cards as `src/worker.ts` from `vite dev` and
 * `vite preview`. Production traffic hits the Worker; this keeps local and
 * preview servers honest for crawlers that do not run JavaScript.
 */

import type { IncomingMessage, ServerResponse } from "node:http"

import type { Plugin } from "vite"
import { previewFor } from "../src/og/preview"

function originFor(req: IncomingMessage): string {
  const hostHeader = req.headers.host ?? "localhost"
  const forwarded = req.headers["x-forwarded-proto"]
  const forwardedProto = Array.isArray(forwarded) ? forwarded[0] : forwarded
  const encrypted =
    "encrypted" in req.socket &&
    Boolean((req.socket as { encrypted?: boolean }).encrypted)
  const proto = forwardedProto || (encrypted ? "https" : "http")
  return `${proto}://${hostHeader}`
}

function previewForNode(req: IncomingMessage) {
  const url = new URL(req.url ?? "/", originFor(req))
  const userAgent = req.headers["user-agent"]
  return previewFor({
    method: req.method ?? "GET",
    pathname: url.pathname,
    search: url.search,
    origin: url.origin,
    userAgent: typeof userAgent === "string" ? userAgent : "",
  })
}

function attach(middlewares: {
  use: (
    fn: (req: IncomingMessage, res: ServerResponse, next: () => void) => void,
  ) => void
}) {
  middlewares.use((req, res, next) => {
    const preview = previewForNode(req)
    if (!preview) {
      next()
      return
    }
    res.statusCode = preview.status
    for (const [name, value] of Object.entries(preview.headers)) {
      res.setHeader(name, value)
    }
    res.end(preview.body ?? undefined)
  })
}

export function openGraph(): Plugin {
  return {
    name: "ring-open-graph",
    configureServer(server) {
      attach(server.middlewares)
    },
    configurePreviewServer(server) {
      attach(server.middlewares)
    },
  }
}
