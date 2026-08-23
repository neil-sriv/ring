import type { PublicLetter, PublicQuestion } from "../client"

export function getUnansweredQuestions(
  loop: PublicLetter,
  userApiId: string | undefined,
): PublicQuestion[] {
  if (!userApiId) {
    return []
  }
  return loop.questions.filter(
    (question) =>
      !question.responses.some(
        (response) => response.participant.api_identifier === userApiId,
      ),
  )
}

export function hasUserReplied(
  loop: PublicLetter,
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

export function getReplyProgress(loop: PublicLetter): ReplyProgress {
  const replied = loop.responders.length
  const total = Math.max(loop.participants.length, replied)
  return { replied, total }
}
