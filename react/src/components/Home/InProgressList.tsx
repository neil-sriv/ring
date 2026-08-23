import { cn } from "@/lib/utils"
import { Link } from "@tanstack/react-router"
import { Check, ChevronRight, Hourglass } from "lucide-react"
import type { MinimalLetter } from "../../client"
import { getLoopDisplayTitle } from "../../util/loopDisplay"
import { getReplyProgress, hasUserReplied } from "../../util/loopReply"
import { formatDueLabel } from "../../util/loopTime"
import { Facepile } from "../Common/Facepile"

function InProgressRow({
  loop,
  userApiId,
}: {
  loop: MinimalLetter
  userApiId: string | undefined
}): JSX.Element {
  const replied = hasUserReplied(loop, userApiId)
  const due = formatDueLabel(loop.send_at)
  const progress = getReplyProgress(loop)

  return (
    <Link
      to="/loops/$loopId"
      params={{ loopId: loop.api_identifier }}
      className="flex items-center gap-3 px-4 py-3 no-underline transition-colors hover:bg-accent"
    >
      <span
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          replied
            ? "bg-success/10 text-success"
            : "bg-muted text-muted-foreground",
        )}
      >
        {replied ? (
          <Check className="h-4 w-4" aria-hidden="true" />
        ) : (
          <Hourglass className="h-4 w-4" aria-hidden="true" />
        )}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">
          {getLoopDisplayTitle(loop)}
        </span>
        <span className="block truncate text-xs text-muted-foreground">
          {loop.group.name} &middot;{" "}
          {replied ? "You've replied" : "No questions yet"} &middot; {due.label}
        </span>
      </span>
      <Facepile users={loop.responders} className="hidden sm:flex" />
      <span className="shrink-0 text-xs text-muted-foreground">
        {progress.replied}/{progress.total}
      </span>
      <ChevronRight
        className="h-4 w-4 shrink-0 text-muted-foreground/50"
        aria-hidden="true"
      />
    </Link>
  )
}

export function InProgressList({
  loops,
  userApiId,
}: {
  loops: MinimalLetter[]
  userApiId: string | undefined
}): JSX.Element {
  return (
    <div className="divide-y overflow-hidden rounded-lg border bg-card shadow-xs">
      {loops.map((loop) => (
        <InProgressRow
          key={loop.api_identifier}
          loop={loop}
          userApiId={userApiId}
        />
      ))}
    </div>
  )
}
