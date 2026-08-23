import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Link } from "@tanstack/react-router"
import { Clock, PenLine } from "lucide-react"
import type { PublicLetter, PublicQuestion } from "../../client"
import { getLoopDisplayTitle } from "../../util/loopDisplay"
import { getReplyProgress } from "../../util/loopReply"
import { formatDueLabel } from "../../util/loopTime"

export function NeedsReplyCard({
  loop,
  unansweredQuestions,
}: {
  loop: PublicLetter
  unansweredQuestions: PublicQuestion[]
}): JSX.Element {
  const due = formatDueLabel(loop.send_at)
  const progress = getReplyProgress(loop)
  const repliedRatio =
    progress.total > 0 ? progress.replied / progress.total : 0
  const teaser = unansweredQuestions[0]?.question_text
  const unansweredCount = unansweredQuestions.length

  return (
    <Link
      to="/loops/$loopId"
      params={{ loopId: loop.api_identifier }}
      className="group block h-full no-underline"
    >
      <Card className="flex h-full flex-col gap-3 p-5 transition-shadow hover:shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <span className="min-w-0 truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {loop.group.name}
          </span>
          <span
            className={cn(
              "inline-flex shrink-0 items-center gap-1 text-xs font-medium",
              due.isUrgent ? "text-warning" : "text-muted-foreground",
            )}
          >
            <Clock className="h-3 w-3" aria-hidden="true" />
            {due.label}
          </span>
        </div>

        <h3 className="line-clamp-2 min-w-0 break-words font-display text-lg font-medium leading-snug">
          {getLoopDisplayTitle(loop)}
        </h3>

        {teaser && (
          <blockquote className="line-clamp-2 border-l-2 pl-3 font-display text-sm italic leading-relaxed text-muted-foreground">
            {teaser}
          </blockquote>
        )}

        <div className="mt-auto flex flex-col gap-3 pt-2">
          <div
            className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-label="Participants who replied"
            aria-valuemin={0}
            aria-valuemax={progress.total}
            aria-valuenow={progress.replied}
          >
            <div
              className="h-full rounded-full bg-success"
              style={{ width: `${Math.round(repliedRatio * 100)}%` }}
            />
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-muted-foreground">
              {progress.replied} of {progress.total} replied
            </span>
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:underline">
              <PenLine className="h-4 w-4" aria-hidden="true" />
              Answer {unansweredCount} question
              {unansweredCount !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </Card>
    </Link>
  )
}
