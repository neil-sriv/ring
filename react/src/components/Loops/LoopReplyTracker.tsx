import { Check, Clock } from "lucide-react"
import type { PublicLetter, UserUnlinked } from "../../client"

interface ParticipantReplyStatus {
  participant: UserUnlinked
  answeredCount: number
  hasReplied: boolean
}

export function getParticipantReplyStatuses(
  loop: PublicLetter,
): ParticipantReplyStatus[] {
  const answeredCounts = new Map<string, number>()
  for (const question of loop.questions) {
    const respondentIds = new Set(
      question.responses.map((response) => response.participant.api_identifier),
    )
    for (const apiId of respondentIds) {
      answeredCounts.set(apiId, (answeredCounts.get(apiId) ?? 0) + 1)
    }
  }

  const responderIds = new Set(
    loop.responders.map((responder) => responder.api_identifier),
  )

  // Roster is the letter's participants; also keep anyone who responded but
  // is no longer listed as a participant so counts stay consistent.
  const roster = new Map<string, UserUnlinked>()
  for (const participant of loop.participants) {
    roster.set(participant.api_identifier, participant)
  }
  for (const responder of loop.responders) {
    if (!roster.has(responder.api_identifier)) {
      roster.set(responder.api_identifier, responder)
    }
  }

  return [...roster.values()]
    .map((participant) => {
      const answeredCount = answeredCounts.get(participant.api_identifier) ?? 0
      return {
        participant,
        answeredCount,
        hasReplied:
          answeredCount > 0 || responderIds.has(participant.api_identifier),
      }
    })
    .sort((a, b) => a.participant.name.localeCompare(b.participant.name))
}

function ReplyStatusChip({
  status,
  questionCount,
}: {
  status: ParticipantReplyStatus
  questionCount: number
}) {
  const showAnsweredCount = status.hasReplied && questionCount > 0
  const chipTitle = showAnsweredCount
    ? `${status.participant.name} answered ${
        status.answeredCount
      } of ${questionCount} question${questionCount !== 1 ? "s" : ""}`
    : status.hasReplied
      ? `${status.participant.name} has replied`
      : `${status.participant.name} hasn't replied yet`

  return (
    <li
      title={chipTitle}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
        status.hasReplied
          ? "border-success/25 bg-success/10 text-success"
          : "border-border bg-muted text-muted-foreground"
      }`}
    >
      {status.hasReplied ? (
        <Check className="h-3 w-3 shrink-0" aria-hidden="true" />
      ) : (
        <Clock className="h-3 w-3 shrink-0" aria-hidden="true" />
      )}
      <span>{status.participant.name}</span>
      {showAnsweredCount && (
        <span className="opacity-75">
          {status.answeredCount}/{questionCount}
        </span>
      )}
    </li>
  )
}

export function LoopReplyTracker({ loop }: { loop: PublicLetter }) {
  if (loop.status === "UPCOMING") {
    return null
  }

  const statuses = getParticipantReplyStatuses(loop)
  if (statuses.length === 0) {
    return null
  }

  const replied = statuses.filter((status) => status.hasReplied)
  const pending = statuses.filter((status) => !status.hasReplied)
  const questionCount = loop.questions.length
  const repliedRatio =
    statuses.length > 0 ? replied.length / statuses.length : 0

  return (
    <div className="w-full rounded-lg border bg-card p-5 shadow-xs">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-base font-semibold text-foreground">Replies</h3>
        <p className="text-sm text-muted-foreground">
          {replied.length} of {statuses.length} participant
          {statuses.length !== 1 ? "s" : ""} replied
        </p>
      </div>

      <div
        className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-label="Participants who replied"
        aria-valuemin={0}
        aria-valuemax={statuses.length}
        aria-valuenow={replied.length}
      >
        <div
          className="h-full rounded-full bg-success transition-all duration-300"
          style={{ width: `${Math.round(repliedRatio * 100)}%` }}
        />
      </div>

      {replied.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            Replied ({replied.length})
          </p>
          <ul className="flex flex-wrap gap-2">
            {replied.map((status) => (
              <ReplyStatusChip
                key={status.participant.api_identifier}
                status={status}
                questionCount={questionCount}
              />
            ))}
          </ul>
        </div>
      )}

      {pending.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            {loop.status === "SENT" ? "Didn't reply" : "Waiting on"} (
            {pending.length})
          </p>
          <ul className="flex flex-wrap gap-2">
            {pending.map((status) => (
              <ReplyStatusChip
                key={status.participant.api_identifier}
                status={status}
                questionCount={questionCount}
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
