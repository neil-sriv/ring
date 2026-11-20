import type { PublicLetter, UserUnlinked } from "../client"

/** Mirrors `LATE_QUESTION_CUTOFF` in `ring/letters/constants.py`. The server decides. */
export const LATE_QUESTION_CUTOFF_MS = 24 * 60 * 60 * 1000

export const LATE_QUESTION_CUTOFF_REASON =
  "It's too close to the send time to add a question."

/**
 * True when an in-progress loop is within 24 hours of send_at, including
 * a send time that has already passed. Upcoming loops and a missing
 * send_at are not cut off. Display only.
 */
export function isLateQuestionCutoffReached(
  loop: Pick<PublicLetter, "status" | "send_at">,
  now: Date = new Date(),
): boolean {
  if (loop.status !== "IN_PROGRESS" || !loop.send_at) {
    return false
  }
  const sendAt = new Date(loop.send_at)
  if (Number.isNaN(sendAt.getTime())) {
    return false
  }
  return sendAt.getTime() <= now.getTime() + LATE_QUESTION_CUTOFF_MS
}

function displayName(person: UserUnlinked): string {
  const name = person.name.trim()
  return name.length > 0 ? name : person.email
}

function formatNameList(names: string[]): string {
  if (names.length <= 1) {
    return names[0] ?? ""
  }
  if (names.length === 2) {
    return `${names[0]} and ${names[1]}`
  }
  return `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`
}

/**
 * Who has already replied, and who the server will notify.
 * `responders` is the users who have responded; `participants` is the roster.
 * Inbox and push go to participants who already replied, except the
 * question's author. This composer posts as `authorApiId`, so that person
 * stays in the replied count and is left out of the "will be told" list.
 * Until the author is known, the notice does not claim anyone will be told.
 */
export function lateQuestionReplyNotice(
  loop: PublicLetter,
  authorApiId?: string,
): string {
  const participantIds = new Set(
    loop.participants.map((person) => person.api_identifier),
  )
  const replied = loop.responders
    .filter((person) => participantIds.has(person.api_identifier))
    .sort((a, b) => displayName(a).localeCompare(displayName(b)))
  const count = `${replied.length} of ${loop.participants.length} people have already replied`
  const placement = "It will appear at the top of the letter."
  const told =
    authorApiId === undefined
      ? []
      : replied.filter((person) => person.api_identifier !== authorApiId)
  if (told.length === 0) {
    return `${count}. ${placement}`
  }
  return `${count}. ${formatNameList(
    told.map(displayName),
  )} will be told about this question. ${placement}`
}
