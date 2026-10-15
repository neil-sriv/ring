import assert from "node:assert/strict"
import test from "node:test"

import { encodeBody, sendHeartbeat, signBody } from "./heartbeat.ts"

const VECTOR_BODY =
  '{"instance":"ring-api","intervalSeconds":300,"kind":"heartbeat","serviceId":"ring-api","status":"ok","version":"abc"}'
const VECTOR_SIG =
  "90f343d950cb9ae2573067b446ca0bd7d59c668f54588c3f5fd7078584220ceb"

test("body encoding is sorted and compact", () => {
  assert.equal(
    encodeBody({
      version: "abc",
      status: "ok",
      serviceId: "ring-api",
      kind: "heartbeat",
      intervalSeconds: 300,
      instance: "ring-api",
    }),
    VECTOR_BODY,
  )
})

test("hmac matches the documented construction", async () => {
  assert.equal(
    await signBody("test-secret", "1700000000", VECTOR_BODY),
    VECTOR_SIG,
  )
})

test("send does nothing when any heartbeat env var is missing", async () => {
  let calls = 0
  const original = globalThis.fetch
  globalThis.fetch = async () => {
    calls += 1
    return new Response()
  }
  try {
    await sendHeartbeat({}, "ok")
    await sendHeartbeat(
      { HEARTBEAT_URL: " https://example.test/api/heartbeat " },
      "ok",
    )
    await sendHeartbeat(
      {
        HEARTBEAT_URL: "https://example.test/api/heartbeat",
        HEARTBEAT_KEY_ID: "ring-frontend",
        HEARTBEAT_SECRET: "   ",
      },
      "ok",
    )
    assert.equal(calls, 0)
  } finally {
    globalThis.fetch = original
  }
})

test("send posts the signed body and not the secret", async () => {
  let captured: { url: string; init: RequestInit } | undefined
  const original = globalThis.fetch
  globalThis.fetch = async (input, init) => {
    captured = { url: String(input), init: init ?? {} }
    return new Response(null, { status: 204 })
  }
  try {
    await sendHeartbeat(
      {
        HEARTBEAT_URL: "https://example.test/api/heartbeat",
        HEARTBEAT_KEY_ID: "ring-frontend",
        HEARTBEAT_SECRET: "test-secret",
      },
      "ok",
      1700000000,
    )
  } finally {
    globalThis.fetch = original
  }
  assert.ok(captured)
  assert.equal(captured.url, "https://example.test/api/heartbeat")
  const headers = new Headers(captured.init.headers)
  assert.equal(headers.get("X-Heartbeat-Key-Id"), "ring-frontend")
  assert.equal(headers.get("X-Heartbeat-Timestamp"), "1700000000")
  assert.equal(
    String(captured.init.body).includes('"intervalSeconds":300'),
    true,
  )
  assert.equal(captured.init.body?.toString().includes("test-secret"), false)
  assert.notEqual(headers.get("X-Heartbeat-Signature"), "test-secret")
  const signature = await signBody(
    "test-secret",
    "1700000000",
    String(captured.init.body),
  )
  assert.equal(headers.get("X-Heartbeat-Signature"), signature)
})
