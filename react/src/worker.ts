/**
 * Cloudflare entry point in front of the built SPA.
 *
 * Production serves `/*` from this Worker's static assets. Link-preview
 * crawlers read Open Graph tags out of the first HTML response and never run
 * JavaScript, so they get a head-only card instead of the app shell. Anything
 * else falls through to the assets, which carry a baseline card of their own
 * in `index.html`.
 */

import { sendHeartbeat } from "./heartbeat"
import { previewFor } from "./og/preview"

interface AssetFetcher {
  fetch(request: Request): Promise<Response>
}

interface Env {
  ASSETS: AssetFetcher
  HEARTBEAT_URL?: string
  HEARTBEAT_KEY_ID?: string
  HEARTBEAT_SECRET?: string
}

const worker = {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    const preview = previewFor({
      method: request.method,
      pathname: url.pathname,
      search: url.search,
      origin: url.origin,
      userAgent: request.headers.get("user-agent") ?? "",
    })
    if (!preview) {
      return env.ASSETS.fetch(request)
    }
    return new Response(preview.body, {
      status: preview.status,
      headers: preview.headers,
    })
  },
  // Every five minutes. No-op until the three HEARTBEAT_* Worker secrets exist.
  async scheduled(_event: unknown, env: Env): Promise<void> {
    await sendHeartbeat(env, "ok")
  },
}

export default worker
