/**
 * Blindfold push heartbeat for the ring-frontend Worker.
 *
 * `@neilsriv/uptime` is not on npm. This is the documented HMAC
 * protocol: POST the ingest URL, HMAC-SHA256 over
 * `timestamp + "\n" + body`, lowercase hex. Headers are
 * `X-Heartbeat-Key-Id`, `X-Heartbeat-Timestamp`, and
 * `X-Heartbeat-Signature`. `serviceId` is `ring-frontend`, the
 * provisioned key id.
 *
 * No request unless `HEARTBEAT_URL`, `HEARTBEAT_KEY_ID`, and
 * `HEARTBEAT_SECRET` are all set. Beats report `intervalSeconds` 300,
 * matching the five-minute cron, so Blindfold marks them stale after
 * about 12.5 minutes.
 */

import { serviceName } from "./observability"

export const SERVICE_ID = "ring-frontend"
export const INTERVAL_SECONDS = 300

export type HeartbeatStatus = "ok" | "degraded" | "down" | "stopping"

export interface HeartbeatEnv {
  HEARTBEAT_URL?: string
  HEARTBEAT_KEY_ID?: string
  HEARTBEAT_SECRET?: string
}

export function encodeBody(payload: Record<string, string | number>): string {
  const ordered: Record<string, string | number> = {}
  for (const key of Object.keys(payload).sort()) {
    ordered[key] = payload[key]
  }
  return JSON.stringify(ordered)
}

export async function signBody(
  secret: string,
  timestamp: string,
  body: string,
): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  )
  const mac = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(`${timestamp}\n${body}`),
  )
  return [...new Uint8Array(mac)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
}

function logFailure(): void {
  console.error(
    JSON.stringify({ service: serviceName, msg: "heartbeat failed" }),
  )
}

export async function sendHeartbeat(
  env: HeartbeatEnv,
  status: HeartbeatStatus,
  nowSeconds: number = Math.floor(Date.now() / 1000),
): Promise<void> {
  const url = env.HEARTBEAT_URL?.trim()
  const keyId = env.HEARTBEAT_KEY_ID?.trim()
  const secret = env.HEARTBEAT_SECRET?.trim()
  if (!url || !keyId || !secret) {
    return
  }
  const body = encodeBody({
    instance: SERVICE_ID,
    intervalSeconds: INTERVAL_SECONDS,
    kind: "heartbeat",
    serviceId: SERVICE_ID,
    status,
    version: "",
  })
  const timestamp = String(nowSeconds)
  let signature: string
  try {
    signature = await signBody(secret, timestamp, body)
  } catch {
    logFailure()
    return
  }
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Heartbeat-Key-Id": keyId,
        "X-Heartbeat-Signature": signature,
        "X-Heartbeat-Timestamp": timestamp,
      },
      body,
      signal: AbortSignal.timeout(5000),
    })
    if (!response.ok) {
      logFailure()
    }
  } catch {
    logFailure()
  }
}
