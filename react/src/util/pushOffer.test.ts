import assert from "node:assert/strict"
import test from "node:test"

import {
  type PushClientFacts,
  pushOfferCopy,
  pushOfferKind,
} from "./pushOffer.ts"

function facts(overrides: Partial<PushClientFacts> = {}): PushClientFacts {
  return {
    userAgent:
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
    platform: "Linux x86_64",
    maxTouchPoints: 0,
    standaloneDisplay: false,
    hasServiceWorker: true,
    hasPushManager: true,
    hasNotification: true,
    permission: "default",
    ...overrides,
  }
}

test("a normal desktop tab can subscribe without being installed", () => {
  assert.equal(pushOfferKind(facts()), "enable")
  assert.equal(pushOfferKind(facts({ standaloneDisplay: true })), "enable")
})

test("Android Chrome in a tab can subscribe without Add to Home Screen", () => {
  const kind = pushOfferKind(
    facts({
      userAgent:
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
      platform: "Linux armv8l",
      maxTouchPoints: 5,
      standaloneDisplay: false,
    }),
  )
  assert.equal(kind, "enable")
  assert.doesNotMatch(pushOfferCopy(kind), /Home Screen|install/i)
  assert.match(pushOfferCopy(kind), /web app/)
})

test("an already-granted browser is enabled, and a blocked one is denied", () => {
  assert.equal(pushOfferKind(facts({ permission: "granted" })), "enabled")
  assert.equal(pushOfferKind(facts({ permission: "denied" })), "denied")
})

test("iOS Safari in a tab cannot background-push and says Add to Home Screen", () => {
  const kind = pushOfferKind(
    facts({
      userAgent:
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 Version/18.5 Mobile/15E148 Safari/604.1",
      platform: "iPhone",
      maxTouchPoints: 5,
      standaloneDisplay: false,
      hasServiceWorker: true,
      hasPushManager: false,
      hasNotification: false,
      permission: "unknown",
    }),
  )
  assert.equal(kind, "ios_home_screen")
  const copy = pushOfferCopy(kind)
  assert.match(copy, /Add to Home Screen/)
  assert.match(copy, /inbox/)
  assert.doesNotMatch(copy, /this tab can/i)
})

test("iPadOS desktop user agent without Push is the Home Screen case", () => {
  assert.equal(
    pushOfferKind(
      facts({
        userAgent:
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.5 Safari/605.1.15",
        platform: "MacIntel",
        maxTouchPoints: 5,
        hasPushManager: false,
        hasNotification: false,
        permission: "unknown",
      }),
    ),
    "ios_home_screen",
  )
})

test("iOS Home Screen web app with Push can subscribe", () => {
  assert.equal(
    pushOfferKind(
      facts({
        userAgent:
          "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
        platform: "iPhone",
        maxTouchPoints: 5,
        standaloneDisplay: true,
        permission: "default",
      }),
    ),
    "enable",
  )
})

test("a Mac Safari tab with Push is not treated as iOS", () => {
  assert.equal(
    pushOfferKind(
      facts({
        userAgent:
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.5 Safari/605.1.15",
        platform: "MacIntel",
        maxTouchPoints: 0,
      }),
    ),
    "enable",
  )
})

test("a browser missing Push and not iOS stays unsupported", () => {
  const kind = pushOfferKind(
    facts({
      hasServiceWorker: false,
      hasPushManager: false,
      hasNotification: false,
      permission: "unknown",
    }),
  )
  assert.equal(kind, "unsupported")
  assert.match(pushOfferCopy(kind), /inbox/)
})
