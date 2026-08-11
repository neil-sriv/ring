/**
 * Paths that a signed-out user has to be able to reach, including the
 * one-time-token links we email out for password resets and invites.
 *
 * A leftover `access_token` in localStorage (expired sessions are never cleared
 * until a request fails) must not gate or redirect away from these paths, or
 * the emailed token is dropped before the user can use it.
 */
const PUBLIC_AUTH_PATH_PATTERNS = [
  /^\/login\/?$/,
  /^\/reset-password(\/.*)?$/,
  /^\/register\/.+$/,
]

export function isPublicAuthPath(pathname: string): boolean {
  return PUBLIC_AUTH_PATH_PATTERNS.some((pattern) => pattern.test(pathname))
}
