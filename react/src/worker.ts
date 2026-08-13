/**
 * Cloudflare entry point in front of the built SPA.
 *
 * Production serves `/*` from this Worker's static assets, so the nginx
 * user-agent routing in `prod.nginx.conf` only applies on the EC2 rollback
 * path. Link-preview crawlers (Slack, Discord, iMessage, ...) read Open Graph
 * tags out of the first HTML response and never run JavaScript, so they get the
 * API's `/unfurl` card instead of the app shell. Anything else - and any
 * failure reaching the API - falls through to the shell, which carries a
 * baseline card of its own in `index.html`.
 */

interface AssetFetcher {
  fetch(request: Request): Promise<Response>
}

interface Env {
  ASSETS: AssetFetcher
  UNFURL_API_ORIGIN: string
}

/**
 * iMessage sends a Safari string with `facebookexternalhit/1.1 Facebot
 * Twitterbot/1.0` appended, which is why those three appear here.
 */
const LINK_PREVIEW_AGENTS =
  /Slackbot|Discordbot|facebookexternalhit|Facebot|Twitterbot|WhatsApp|TelegramBot|LinkedInBot|SkypeUriPreview|redditbot|Iframely|Embedly|Cardyb|Mastodon/i

const FILE_PATH = /\.[a-z0-9]{1,6}$/i

/** Crawlers fetch `og:image` next, so asset requests keep hitting the file. */
function isPageRequest(pathname: string): boolean {
  return !FILE_PATH.test(pathname)
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    const userAgent = request.headers.get("user-agent") ?? ""

    if (!LINK_PREVIEW_AGENTS.test(userAgent) || !isPageRequest(url.pathname)) {
      return env.ASSETS.fetch(request)
    }

    try {
      const card = await fetch(
        `${env.UNFURL_API_ORIGIN}/api/v1/unfurl${url.pathname}`,
        { headers: { "user-agent": userAgent } },
      )
      if (card.ok) {
        const headers = new Headers(card.headers)
        // Cloudflare ignores Vary, so a cached card could otherwise be handed
        // to a browser on the same URL and replace the app with a dead page.
        headers.set("cache-control", "private, no-store")
        return new Response(card.body, { status: card.status, headers })
      }
    } catch {
      // Fall through to the shell rather than failing the crawler's request.
    }

    return env.ASSETS.fetch(request)
  },
}
