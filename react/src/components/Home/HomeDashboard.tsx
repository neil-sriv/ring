import { useSuspenseQuery } from "@tanstack/react-query"
import { listDashboardLettersLettersLettersDashboardGetOptions } from "../../client/@tanstack/react-query.gen"
import { LoopsGrid } from "../Loops/LoopsGrid"

export function HomeDashboard() {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  })
  const recently_completed = dashboardLoops.data.recently_completed
  const in_progress = dashboardLoops.data.in_progress
  const upcoming = dashboardLoops.data.upcoming

  return (
    <div className="flex justify-center w-full bg-background/60 backdrop-blur-sm">
      <div className="max-w-[1200px] w-full px-4 py-8">
        <div className="flex flex-col gap-8 items-stretch w-full">
          <h1 className="text-center text-foreground text-xl font-bold tracking-tight py-4 border-b border-border">
            Dashboard
          </h1>
          {recently_completed.length > 0 && (
            <LoopsGrid
              loops={recently_completed.sort(
                (a, b) =>
                  new Date(a.send_at).getTime() - new Date(b.send_at).getTime(),
              )}
              heading="Published Issues"
              includeGroupName={true}
              showLoopTypeLabel={true}
            />
          )}
          {in_progress.length > 0 && (
            <LoopsGrid
              loops={in_progress.sort(
                (a, b) =>
                  new Date(a.send_at).getTime() - new Date(b.send_at).getTime(),
              )}
              heading="In Progress"
              subheading="Add your response now!"
              includeGroupName={true}
              showLoopTypeLabel={true}
              showResponderCount={true}
            />
          )}
          {upcoming.length > 0 && (
            <LoopsGrid
              loops={upcoming.sort(
                (a, b) =>
                  new Date(a.send_at).getTime() - new Date(b.send_at).getTime(),
              )}
              heading="Upcoming Issues"
              subheading="You can add questions to the upcoming issues before they are available"
              includeGroupName={true}
              showLoopTypeLabel={true}
            />
          )}
        </div>
      </div>
    </div>
  )
}
