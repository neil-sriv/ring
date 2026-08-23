import { Badge } from "@/components/ui/badge"
import { Link } from "@tanstack/react-router"
import { ChevronRight } from "lucide-react"
import type { DashboardLetter } from "../../client"
import { getLoopDisplayTitle } from "../../util/loopDisplay"
import { formatDateChip, formatWeekday } from "../../util/loopTime"

function UpcomingRow({ loop }: { loop: DashboardLetter }): JSX.Element {
  const chip = formatDateChip(loop.send_at)

  return (
    <Link
      to="/loops/$loopId"
      params={{ loopId: loop.api_identifier }}
      className="flex items-center gap-4 px-4 py-3 no-underline transition-colors hover:bg-accent"
    >
      <span className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-md border bg-muted">
        <span className="text-xs font-medium uppercase leading-none text-muted-foreground">
          {chip.month}
        </span>
        <span className="mt-0.5 text-sm font-semibold leading-none">
          {chip.day}
        </span>
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">
          {getLoopDisplayTitle(loop)}
        </span>
        <span className="block truncate text-xs text-muted-foreground">
          {loop.group.name} &middot; Sends {formatWeekday(loop.send_at)}
        </span>
      </span>
      {loop.letter_type === "ADHOC" && (
        <Badge variant="secondary" className="hidden sm:inline-flex">
          One-off
        </Badge>
      )}
      <ChevronRight
        className="h-4 w-4 shrink-0 text-muted-foreground/50"
        aria-hidden="true"
      />
    </Link>
  )
}

export function UpcomingList({
  loops,
}: {
  loops: DashboardLetter[]
}): JSX.Element {
  return (
    <div className="divide-y overflow-hidden rounded-lg border bg-card shadow-xs">
      {loops.map((loop) => (
        <UpcomingRow key={loop.api_identifier} loop={loop} />
      ))}
    </div>
  )
}
