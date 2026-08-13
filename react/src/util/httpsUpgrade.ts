interface PageLocation {
  protocol: string
  host: string
  pathname: string
  search: string
  hash: string
}

/**
 * URL to send the page to when it was loaded over http but talks to an https
 * API on the same host, or null when nothing needs to change.
 *
 * The build bakes an absolute API origin into the bundle, so an http page
 * makes every API call cross-origin and the preflight is rejected. Links we
 * emailed before the backend switched to https land users exactly there.
 *
 * Only the same host is upgraded: an http dev server pointed at an https API
 * on another host is a deliberate setup and is left alone.
 */
export function httpsUpgradeUrl(
  location: PageLocation,
  apiOrigin: string,
): string | null {
  if (location.protocol !== "http:" || !apiOrigin.startsWith("https://")) {
    return null
  }

  let apiHost: string
  try {
    apiHost = new URL(apiOrigin).host
  } catch {
    return null
  }

  if (apiHost !== location.host) {
    return null
  }

  return `https://${location.host}${location.pathname}${location.search}${location.hash}`
}
