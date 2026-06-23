import type { MinimalLetter, PublicLetter } from "../client"

type LoopWithResponderProgress = MinimalLetter | PublicLetter

export function formatResponderProgress(
  loop: LoopWithResponderProgress,
): string | null {
  const requiredResponders = loop.required_responders ?? 0
  const responderCount = loop.responder_count ?? 0

  if (loop.status === "IN_PROGRESS" && requiredResponders > 0) {
    return `${responderCount} of ${requiredResponders} responses needed`
  }

  if (responderCount > 0) {
    return `${responderCount} responder${responderCount !== 1 ? "s" : ""}`
  }

  return null
}
