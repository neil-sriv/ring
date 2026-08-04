/**
 * Resolve API HTTP/WS URLs consistently with main.tsx client config.
 *
 * Empty VITE_API_URL means same-origin (Vite proxy in cloud/local HTTP, or
 * nginx in production builds). A set origin (e.g. https://localhost) is used
 * as-is for OrbStack-style TLS nginx access.
 */

export function getApiOrigin(): string {
  return import.meta.env.VITE_API_URL ?? ""
}

export function apiUrl(path: string): string {
  const origin = getApiOrigin()
  const normalized = path.startsWith("/") ? path : `/${path}`
  return origin ? `${origin}${normalized}` : normalized
}

export function wsUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`
  const origin = getApiOrigin()
  if (origin) {
    return `${origin.replace(/^http/, "ws")}${normalized}`
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  return `${protocol}//${window.location.host}${normalized}`
}
