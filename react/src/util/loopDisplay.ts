import type { MinimalLetter, PublicLetter } from "../client"

export function getLoopDisplayTitle(
  loop: MinimalLetter | PublicLetter,
): string {
  if (loop.title) {
    return loop.title
  }
  if (loop.number) {
    return `Issue #${loop.number}`
  }
  return "Untitled Loop"
}
