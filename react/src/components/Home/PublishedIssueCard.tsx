import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Link } from "@tanstack/react-router"
import type { DashboardLetter } from "../../client"
import { getLoopDisplayTitle } from "../../util/loopDisplay"
import { formatPublishedLabel } from "../../util/loopTime"
import { Facepile } from "../Common/Facepile"

export function PublishedIssueCard({
  loop,
}: {
  loop: DashboardLetter
}): JSX.Element {
  const questionCount = loop.questions.length
  const contributorCount = loop.responders.length

  return (
    <Link
      to="/loops/$loopId"
      params={{ loopId: loop.api_identifier }}
      className="block h-full no-underline"
    >
      <Card className="flex h-full flex-col gap-2.5 p-5 transition-shadow hover:shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <span className="min-w-0 truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {loop.group.name}
          </span>
          {loop.letter_type === "ADHOC" && (
            <Badge variant="secondary">One-off</Badge>
          )}
        </div>
        <h3 className="line-clamp-2 min-w-0 break-words font-display text-lg font-medium leading-snug">
          {getLoopDisplayTitle(loop)}
        </h3>
        <p className="text-xs text-muted-foreground">
          {formatPublishedLabel(loop.send_at)}
        </p>
        <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-2">
          <Facepile users={loop.responders} />
          <span className="text-xs text-muted-foreground">
            {questionCount} question{questionCount !== 1 ? "s" : ""} &middot;{" "}
            {contributorCount} contributor{contributorCount !== 1 ? "s" : ""}
          </span>
        </div>
      </Card>
    </Link>
  )
}
