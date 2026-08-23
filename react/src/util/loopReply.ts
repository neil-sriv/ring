import type { MinimalLetter } from "../client"

export function hasUserReplied(
  loop: MinimalLetter,
  userApiId: string | undefined,
): boolean {
  if (!userApiId) {
    return false
  }
  return loop.responders.some(
    (responder) => responder.api_identifier === userApiId,
  )
}

export interface ReplyProgress {
  replied: number
  total: number
}

export function getReplyProgress(loop: MinimalLetter): ReplyProgress {
  const replied = loop.responders.length
  const total = Math.max(loop.participant_count ?? 0, replied)
  return { replied, total }
}
