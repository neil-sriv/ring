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

const FAILURE_ENV = {
  HEARTBEAT_URL: "https://example.test/api/heartbeat",
  HEARTBEAT_KEY_ID: "kid-do-not-log",
  HEARTBEAT_SECRET: "test-secret",
}
const FAILURE_BODY = encodeBody({
  instance: "ring-frontend",
  intervalSeconds: 300,
  kind: "heartbeat",
  serviceId: "ring-frontend",
  status: "ok",
  version: "",
})
const FAILURE_SIGNATURE = await signBody(
  FAILURE_ENV.HEARTBEAT_SECRET,
  "1700000000",
  FAILURE_BODY,
)

function assertRecord(
  value: unknown,
): asserts value is Record<string, unknown> {
  assert.equal(typeof value, "object")
  assert.notEqual(value, null)
  assert.equal(Array.isArray(value), false)
}

async function loggedFailure(run: () => Promise<void>) {
  const lines: unknown[][] = []
  const original = console.error
  console.error = (...args: unknown[]) => {
    lines.push(args)
  }
  try {
    await run()
  } finally {
    console.error = original
  }
  assert.equal(lines.length, 1)
  const line = lines[0]
  assert.equal(line.length, 1)
  const raw = line[0]
  assert.equal(typeof raw, "string")
  const text = String(raw)
  assert.equal(text.includes(FAILURE_ENV.HEARTBEAT_SECRET), false)
  assert.equal(text.includes(FAILURE_ENV.HEARTBEAT_KEY_ID), false)
  assert.equal(text.includes(FAILURE_SIGNATURE), false)
  const log: unknown = JSON.parse(text)
  assertRecord(log)
  assert.equal(log.service, "ring-frontend")
  assert.equal(log.msg, "heartbeat failed")
  assert.equal(Number.isInteger(log.elapsedMs), true)
  assert.ok(Number(log.elapsedMs) >= 0)
  return log
}

test("a signing error logs sign_error and elapsed ms", async () => {
  let calls = 0
  const originalFetch = globalThis.fetch
  const originalSign = crypto.subtle.sign
  globalThis.fetch = async () => {
    calls += 1
    return new Response()
  }
  crypto.subtle.sign = async () => {
    throw new Error("sign failed")
  }
  try {
    const log = await loggedFailure(() =>
      sendHeartbeat(FAILURE_ENV, "ok", 1700000000),
    )
    assert.equal(calls, 0)
    assert.equal(log.reason, "sign_error")
    assert.equal("status" in log, false)
  } finally {
    globalThis.fetch = originalFetch
    crypto.subtle.sign = originalSign
  }
})

test("a non-OK response logs http_status, status, and elapsed ms", async () => {
  const originalFetch = globalThis.fetch
  let body = ""
  globalThis.fetch = async (_input, init) => {
    body = String(init?.body ?? "")
    return new Response("no", { status: 503 })
  }
  try {
    const log = await loggedFailure(() =>
      sendHeartbeat(FAILURE_ENV, "ok", 1700000000),
    )
    assert.equal(body, FAILURE_BODY)
    assert.equal(log.reason, "http_status")
    assert.equal(log.status, 503)
  } finally {
    globalThis.fetch = originalFetch
  }
})

test("a 5s timeout logs timeout and elapsed ms", async () => {
  const originalTimeout = AbortSignal.timeout
  let timeoutMs = 0
  AbortSignal.timeout = (ms: number) => {
    timeoutMs = ms
    const controller = new AbortController()
    controller.abort(new DOMException("timeout", "TimeoutError"))
    return controller.signal
  }
  try {
    const log = await loggedFailure(() =>
      sendHeartbeat(FAILURE_ENV, "ok", 1700000000),
    )
    assert.equal(timeoutMs, 5000)
    assert.equal(log.reason, "timeout")
    assert.equal("status" in log, false)
  } finally {
    AbortSignal.timeout = originalTimeout
  }
})

test("a fetch exception logs network and elapsed ms", async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => {
    throw new TypeError("fetch failed")
  }
  try {
    const log = await loggedFailure(() =>
      sendHeartbeat(FAILURE_ENV, "ok", 1700000000),
    )
    assert.equal(log.reason, "network")
    assert.equal("status" in log, false)
  } finally {
    globalThis.fetch = originalFetch
  }
})
