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
        <div className="flex flex-col items-center gap-4">
          <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
            Adhoc Loops
          </h3>
          <p className="max-w-[600px] text-center text-muted-foreground">
            Adhoc loops are one-time loops that can be created outside of the
            regular cycle.
          </p>
        </div>
      </div>

      {loops.length > 0 ? (
        <div className="flex w-full flex-col gap-6">
          <div className="w-full">
            <p className="mb-4 text-center text-sm text-muted-foreground">
              Currently showing all adhoc loops.
            </p>
          </div>

          {inProgressLoops.length > 0 && (
            <LoopsGrid
              loops={inProgressLoops}
              heading="In Progress"
              subheading="Add your response now!"
            />
          )}

          {upcomingLoops.length > 0 && (
            <LoopsGrid
              loops={upcomingLoops}
              heading="Upcoming Issues"
              subheading="You can add questions to the upcoming issues before they are available for responses."
            />
          )}

          {publishedLoops.length > 0 && (
            <LoopsGrid
              loops={publishedLoops.sort(
                (a, b) =>
                  new Date(a.send_at).getTime() - new Date(b.send_at).getTime(),
              )}
              heading="Published Issues"
            />
          )}
        </div>
      ) : (
        <div className="w-full text-center">
          <p className="text-muted-foreground">
            No adhoc loops found. Create your first adhoc loop to get started!
          </p>
        </div>
      )}
    </div>
  )
}
