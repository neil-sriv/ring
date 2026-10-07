/**
 * Decide whether a request is a link-preview crawler reading a page, and
 * render the head-only HTML it should receive.
 *
 * The same function serves the Cloudflare Worker (`src/worker.ts`) and the
 * Vite dev/preview middleware (`plugins/open-graph.ts`). Browsers, API calls,
 * and file URLs fall through so the SPA and its assets stay untouched.
 */

import {
  OG_IMAGE_ALT,
  OG_IMAGE_HEIGHT,
  OG_IMAGE_PATH,
  OG_IMAGE_WIDTH,
  SITE_NAME,
  type UnfurlCard,
  cardForPath,
} from "./cards"

/**
 * iMessage sends a Safari string with `facebookexternalhit/1.1 Facebot
 * Twitterbot/1.0` appended, which is why those three appear here.
 */
const LINK_PREVIEW_AGENTS =
  /Slackbot|Discordbot|facebookexternalhit|Facebot|Twitterbot|WhatsApp|TelegramBot|LinkedInBot|SkypeUriPreview|redditbot|Iframely|Embedly|Cardyb|Mastodon/i

/** No app route has a dot in its last segment; `.webmanifest` and friends do. */
const FILE_PATH = /\.[a-z0-9]+$/i

export interface PreviewRequest {
  method: string
  pathname: string
  search: string
  origin: string
  userAgent: string
}

export interface PreviewDecision {
  status: number
  headers: Record<string, string>
  /** Null for HEAD, where the crawler only checks that the URL answers. */
  body: string | null
}

export function isLinkPreviewAgent(userAgent: string): boolean {
  return LINK_PREVIEW_AGENTS.test(userAgent)
}

/** Crawlers fetch `og:image` next, so asset and API requests stay files. */
export function isPageRequest(pathname: string): boolean {
  if (pathname === "/api" || pathname.startsWith("/api/")) {
    return false
  }
  return !FILE_PATH.test(pathname)
}

export function previewFor(request: PreviewRequest): PreviewDecision | null {
  const method = request.method.toUpperCase()
  if (method !== "GET" && method !== "HEAD") {
    return null
  }
  if (
    !isLinkPreviewAgent(request.userAgent) ||
    !isPageRequest(request.pathname)
  ) {
    return null
  }

  const card = cardForPath(request.pathname)
  // Query strings stay off the card. A pasted link can carry a token or a
  // title parameter, and neither is preview text. The path is enough to pick
  // the static copy.
  void request.search
  const canonicalUrl = `${request.origin}${request.pathname}`
  const imageUrl = `${request.origin}${OG_IMAGE_PATH}`
  return {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      // Cloudflare ignores Vary, so a public cache on the page URL can hand
      // this head-only card to a browser and replace the SPA. Chat apps cache
      // on their side; we must not.
      "cache-control": "private, no-store",
    },
    body:
      method === "HEAD"
        ? null
        : renderPreviewDocument({ card, canonicalUrl, imageUrl }),
  }
}

export function renderPreviewDocument(input: {
  card: UnfurlCard
  canonicalUrl: string
  imageUrl: string
}): string {
  const title = escapeHtml(input.card.title)
  const description = escapeHtml(input.card.description)
  const canonicalUrl = escapeHtml(input.canonicalUrl)
  const imageUrl = escapeHtml(input.imageUrl)

  // Slack reads only the first 32KB, so every tag stays at the top of <head>.
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
    <meta name="description" content="${description}" />
    <link rel="canonical" href="${canonicalUrl}" />
    <meta property="og:site_name" content="${SITE_NAME}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="${title}" />
    <meta property="og:description" content="${description}" />
    <meta property="og:url" content="${canonicalUrl}" />
    <meta property="og:image" content="${imageUrl}" />
    <meta property="og:image:width" content="${OG_IMAGE_WIDTH}" />
    <meta property="og:image:height" content="${OG_IMAGE_HEIGHT}" />
    <meta property="og:image:alt" content="${OG_IMAGE_ALT}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${title}" />
    <meta name="twitter:description" content="${description}" />
    <meta name="twitter:image" content="${imageUrl}" />
    <meta name="theme-color" content="#fbfaf7" />
    <link rel="icon" href="/assets/images/favicon.ico" />
    <link rel="apple-touch-icon" href="/assets/images/apple-touch-icon-180x180.png" />
  </head>
  <body>
    <p>${description}</p>
    <p><a href="${canonicalUrl}">${canonicalUrl}</a></p>
  </body>
</html>
`
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;")
}
