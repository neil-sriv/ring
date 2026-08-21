import { Repeat } from "lucide-react"
import type { GroupLinked, MinimalLetter } from "../../client"
import LoopNav from "./LoopNav"
import { LoopsGrid } from "./LoopsGrid"

export function LoopsTab({
  loops,
  group,
}: { loops: MinimalLetter[]; group: GroupLinked }) {
  const publishedLoops = loops.filter((loop) => loop.status === "SENT")
  const inProgressLoops = loops.filter((loop) => loop.status === "IN_PROGRESS")
  const upcomingLoops = loops.filter(
    (loop) => loop.status !== "SENT" && loop.status !== "IN_PROGRESS",
  )

  return (
    <div className="flex w-full flex-col gap-8">
      <div className="w-full">
        <LoopNav loops={loops} group={group} />
      </div>
      {loops.length === 0 && (
        <div className="flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
          <Repeat
            className="h-8 w-8 text-muted-foreground/60"
            strokeWidth={1.5}
          />
          <h3 className="mt-4 font-display text-lg font-medium">
            No loops yet
          </h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Start the first loop to send this group a round of questions.
          </p>
        </div>
      )}
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
  )
}
