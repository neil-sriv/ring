import type { DashboardLetter, DashboardQuestion } from "../client"

export function getUnansweredQuestions(
  loop: DashboardLetter,
  userApiId: string | undefined,
): DashboardQuestion[] {
  if (!userApiId) {
    return []
  }
  return loop.questions.filter(
    (question) => !question.responded_participant_api_ids.includes(userApiId),
  )
}

export function hasUserReplied(
  loop: DashboardLetter,
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

export function getReplyProgress(loop: DashboardLetter): ReplyProgress {
  const replied = loop.responders.length
  const total = Math.max(loop.participant_count, replied)
  return { replied, total }
}
