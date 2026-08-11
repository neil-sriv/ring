/**
 * The frontend's build stamp: which commit this bundle came from, and when
 * it was built.
 *
 * `react/plugins/version-stamp.ts` writes it into the bundle at build time
 * and `dev_util/deploy_status.py` reads it back off a deployed origin.
 * Field names mirror the backend's GET /api/v1/version payload.
 */

export const VERSION_FILE_NAME = "version.json"

export type BuildVersionSource = "workers_ci" | "env" | "git" | "unavailable"

export interface BuildVersion {
  sha: string | null
  short_sha: string | null
  branch: string | null
  built_at: string
  source: BuildVersionSource
  build_uuid: string | null
}

export const GITHUB_COMMIT_URL = "https://github.com/neil-sriv/ring/commit"

/**
 * Read the stamp the running frontend was served with.
 *
 * Unknown paths fall through to the SPA's index.html rather than 404ing,
 * so a non-JSON body means this deploy has no stamp.
 */
export async function fetchBuildVersion(): Promise<BuildVersion> {
  const response = await fetch(`/${VERSION_FILE_NAME}`, { cache: "no-store" })
  if (!response.ok) {
    throw new Error(`version stamp request failed (${response.status})`)
  }
  const body = await response.text()
  if (body.trimStart().startsWith("<")) {
    throw new Error("no version stamp on this deploy")
  }
  return JSON.parse(body) as BuildVersion
}

/** Render an ISO-8601 timestamp as a compact age like `2h 5m ago`. */
export function formatAge(
  timestamp: string | null | undefined,
  now: Date = new Date(),
): string | null {
  if (!timestamp) {
    return null
  }
  const moment = new Date(timestamp)
  if (Number.isNaN(moment.getTime())) {
    return null
  }
  const seconds = Math.floor((now.getTime() - moment.getTime()) / 1000)
  if (seconds < 0) {
    return "just now"
  }
  if (seconds < 60) {
    return `${seconds}s ago`
  }
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes}m ago`
  }
  const hours = Math.floor(minutes / 60)
  if (hours < 24) {
    return `${hours}h ${minutes % 60}m ago`
  }
  const days = Math.floor(hours / 24)
  return `${days}d ${hours % 24}h ago`
}
