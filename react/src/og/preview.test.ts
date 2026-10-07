import assert from "node:assert/strict"
import test from "node:test"

import worker from "../worker"
import { OG_IMAGE_PATH, cardForPath } from "./cards"
import { previewFor, renderPreviewDocument } from "./preview"

const ORIGIN = "https://ring.neilsriv.tech"

function page(pathname: string, userAgent: string, search = "") {
  return previewFor({
    method: "GET",
    pathname,
    search,
    origin: ORIGIN,
    userAgent,
  })
}

test("newsletter, invite, notebook, and group paths use static cards", () => {
  assert.equal(cardForPath("/loops/lttr_abc").title, "A newsletter on Ring")
  assert.equal(
    cardForPath("/loops/lttr_abc").description,
    "Sign in to read this newsletter and everyone else's answers.",
  )
  assert.equal(
    cardForPath("/register/invite-token").title,
    "Your invitation to Ring",
  )
  assert.equal(cardForPath("/documents/doc_abc").title, "A notebook on Ring")
  assert.equal(cardForPath("/groups/grp_abc/settings").title, "A group on Ring")
  assert.equal(cardForPath("/Loops/lttr_abc").title, "A newsletter on Ring")
})

test("every other page uses the site card and names nobody", () => {
  for (const pathname of ["/", "/login", "/reset-password/token", "/search"]) {
    const card = cardForPath(pathname)
    assert.equal(card.title, "Ring")
    assert.equal(
      card.description,
      "Ring asks your group the same few questions on a cadence, then collects everyone's answers into one newsletter.",
    )
  }
})

test("a letter link does not include the letter body or a caller-supplied title", () => {
  const preview = page(
    "/loops/lttr_secret",
    "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
    "?s=share-token&title=Private+minutes",
  )
  assert.ok(preview)
  const html = preview.body ?? ""
  assert.match(html, /property="og:title" content="A newsletter on Ring"/)
  assert.match(
    html,
    /property="og:description" content="Sign in to read this newsletter and everyone else&#x27;s answers\."/,
  )
  assert.match(
    html,
    new RegExp(`property="og:image" content="${ORIGIN}${OG_IMAGE_PATH}"`),
  )
  assert.doesNotMatch(html, /Private minutes/)
  assert.doesNotMatch(html, /share-token/)
  assert.equal(html.includes("?s="), false)
  assert.ok(html.length < 32 * 1024)
  assert.equal(preview.headers["cache-control"], "private, no-store")
})

test("iMessage, Facebook, and Twitter user agents receive a card", () => {
  const agents = [
    "Mozilla/5.0 facebookexternalhit/1.1 Facebot Twitterbot/1.0",
    "facebookexternalhit/1.1",
    "Twitterbot/1.0",
  ]
  for (const userAgent of agents) {
    const preview = page("/groups/grp_abc", userAgent)
    assert.ok(preview, userAgent)
    assert.match(
      preview.body ?? "",
      /property="og:title" content="A group on Ring"/,
    )
  }
})

test("browsers, files, and the API fall through", () => {
  assert.equal(page("/loops/lttr_abc", "Mozilla/5.0"), null)
  assert.equal(
    page("/assets/images/og-card.png", "Slackbot-LinkExpanding 1.0"),
    null,
  )
  assert.equal(page("/manifest.webmanifest", "facebookexternalhit/1.1"), null)
  assert.equal(page("/api/v1/letters/lttr_abc", "Twitterbot/1.0"), null)
  assert.equal(
    previewFor({
      method: "POST",
      pathname: "/loops/lttr_abc",
      search: "",
      origin: ORIGIN,
      userAgent: "Slackbot-LinkExpanding 1.0",
    }),
    null,
  )
})

test("HEAD answers with headers and no body", () => {
  const preview = previewFor({
    method: "HEAD",
    pathname: "/register/tok",
    search: "",
    origin: ORIGIN,
    userAgent: "Slackbot-LinkExpanding 1.0",
  })
  assert.ok(preview)
  assert.equal(preview.body, null)
  assert.equal(preview.headers["content-type"], "text/html; charset=utf-8")
})

test("markup escapes titles and urls", () => {
  const html = renderPreviewDocument({
    card: { title: `A <b>title</b> & "quotes"`, description: "it's fine" },
    canonicalUrl: `${ORIGIN}/loops/lttr_x?q="1"`,
    imageUrl: `${ORIGIN}${OG_IMAGE_PATH}`,
  })
  assert.match(
    html,
    /property="og:title" content="A &lt;b&gt;title&lt;\/b&gt; &amp; &quot;quotes&quot;"/,
  )
  assert.match(html, /content="it&#x27;s fine"/)
  assert.match(
    html,
    /og:url" content="https:\/\/ring\.neilsriv\.tech\/loops\/lttr_x\?q=&quot;1&quot;"/,
  )
})

test("the worker serves crawlers a card and browsers the asset", async () => {
  let assetFetches = 0
  const env = {
    ASSETS: {
      fetch: async () => {
        assetFetches += 1
        return new Response("app-shell", {
          headers: { "content-type": "text/html" },
        })
      },
    },
  }

  const card = await worker.fetch(
    new Request(`${ORIGIN}/loops/lttr_abc`, {
      headers: { "user-agent": "Slackbot-LinkExpanding 1.0" },
    }),
    env,
  )
  assert.equal(card.status, 200)
  assert.equal(card.headers.get("cache-control"), "private, no-store")
  assert.match(await card.text(), /og:title" content="A newsletter on Ring"/)
  assert.equal(assetFetches, 0)

  const app = await worker.fetch(
    new Request(`${ORIGIN}/loops/lttr_abc`, {
      headers: { "user-agent": "Mozilla/5.0" },
    }),
    env,
  )
  assert.equal(await app.text(), "app-shell")
  assert.equal(assetFetches, 1)
})
