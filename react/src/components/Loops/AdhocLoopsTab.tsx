import { Mail } from "lucide-react"
import type { GroupLinked, MinimalLetter } from "../../client"
import AdhocLoopNav from "./AdhocLoopNav"
import { LoopsGrid } from "./LoopsGrid"

export function AdhocLoopsTab({
  loops,
  group,
}: { loops: MinimalLetter[]; group: GroupLinked }) {
  const inProgressLoops = loops.filter((loop) => loop.status === "IN_PROGRESS")
  const upcomingLoops = loops.filter(
    (loop) => loop.status !== "SENT" && loop.status !== "IN_PROGRESS",
  )
  const publishedLoops = loops.filter((loop) => loop.status === "SENT")

  return (
    <div className="flex w-full flex-col gap-8">
      <div className="w-full">
        <AdhocLoopNav loops={loops} group={group} />
      </div>

      <div className="w-full">
        <h3 className="text-base font-semibold">Adhoc Loops</h3>
        <p className="mt-1 max-w-prose text-sm text-muted-foreground">
          Adhoc loops are one-time loops that can be created outside of the
          regular cycle.
        </p>
      </div>

      {loops.length > 0 ? (
        <div className="flex w-full flex-col gap-8">
          {inProgressLoops.length > 0 && (
            <LoopsGrid
              loops={inProgressLoops}
              heading="In Progress"
              subheading="Add your response now."
              showResponderCount={true}
            />
          )}

          {upcomingLoops.length > 0 && (
            <LoopsGrid
              loops={upcomingLoops}
              heading="Upcoming Issues"
              subheading="You can add questions to the upcoming issues before they are available for responses."
              showResponderCount={true}
            />
          )}

          {publishedLoops.length > 0 && (
            <LoopsGrid
              loops={publishedLoops.sort(
                (a, b) =>
                  new Date(a.send_at).getTime() - new Date(b.send_at).getTime(),
              )}
              heading="Published Issues"
              showResponderCount={true}
            />
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
          <Mail
            className="h-8 w-8 text-muted-foreground/60"
            strokeWidth={1.5}
          />
          <h3 className="mt-4 font-display text-lg font-medium">
            No adhoc loops yet
          </h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Create your first adhoc loop to send a one-off letter to this
            group.
          </p>
        </div>
      )}
    </div>
  )
}
