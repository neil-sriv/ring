import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Link } from "@tanstack/react-router"
import { Clock, PenLine } from "lucide-react"
import type { MinimalLetter } from "../../client"
import { getLoopDisplayTitle } from "../../util/loopDisplay"
import { formatResponderProgress } from "../../util/loopResponderProgress"
import { formatDueLabel } from "../../util/loopTime"

export function NeedsReplyCard({
  loop,
}: {
  loop: MinimalLetter
}): JSX.Element {
  const due = formatDueLabel(loop.send_at)
  const progressLabel = formatResponderProgress(loop)
  const requiredResponders = loop.required_responders ?? 0
  const responderCount = loop.responder_count ?? 0
  const repliedRatio =
    requiredResponders > 0
      ? Math.min(responderCount / requiredResponders, 1)
      : 0

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

        <div className="mt-auto flex flex-col gap-3 pt-2">
          {requiredResponders > 0 && (
            <div
              className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
              role="progressbar"
              aria-label="Responses received"
              aria-valuemin={0}
              aria-valuemax={requiredResponders}
              aria-valuenow={responderCount}
            >
              <div
                className="h-full rounded-full bg-success"
                style={{ width: `${Math.round(repliedRatio * 100)}%` }}
              />
            </div>
          )}
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-muted-foreground">
              {progressLabel ?? "No replies yet"}
            </span>
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:underline">
              <PenLine className="h-4 w-4" aria-hidden="true" />
              Write your reply
            </span>
          </div>
        </div>
      </Card>
    </Link>
  )
}
