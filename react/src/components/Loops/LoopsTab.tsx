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
      {inProgressLoops.length > 0 && (
        <LoopsGrid
          loops={inProgressLoops}
          heading="In Progress"
          subheading="Add your response now!"
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
