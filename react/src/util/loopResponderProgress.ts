import type { MinimalLetter, PublicLetter } from "../client"

type LoopWithResponderProgress = MinimalLetter | PublicLetter

export function formatResponderProgress(
  loop: LoopWithResponderProgress,
): string | null {
  if (
    loop.status === "IN_PROGRESS" &&
    loop.required_responders > 0
  ) {
    return `${loop.responder_count} of ${loop.required_responders} responses needed`
  }

  if (loop.responder_count > 0) {
    return `${loop.responder_count} responder${loop.responder_count !== 1 ? "s" : ""}`
  }

  return null
}
