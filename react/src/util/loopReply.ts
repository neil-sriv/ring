import type { MinimalLetter, PublicLetter } from "../client"

export function hasUserReplied(
  loop: MinimalLetter | PublicLetter,
  userApiId: string | undefined,
): boolean {
  if (!userApiId) {
    return false
  }
  return loop.responders.some(
    (responder) => responder.api_identifier === userApiId,
  )
}
