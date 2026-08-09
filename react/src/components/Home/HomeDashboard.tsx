import { Button } from "@/components/ui/button"
import { useSuspenseQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { useState } from "react"
import { listDashboardLettersLettersLettersDashboardGetOptions } from "../../client/@tanstack/react-query.gen"
import AddGroup from "../Groups/AddGroup"
import { LoopsGrid } from "../Loops/LoopsGrid"

export function HomeDashboard() {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  })
  const recently_completed = dashboardLoops.data.recently_completed
  const in_progress = dashboardLoops.data.in_progress
  const upcoming = dashboardLoops.data.upcoming
  const [isAddGroupOpen, setIsAddGroupOpen] = useState(false)

  const isEmpty =
    recently_completed.length === 0 &&
    in_progress.length === 0 &&
    upcoming.length === 0

  return (
    <div className="flex justify-center w-full bg-background/60 backdrop-blur-sm">
      <div className="max-w-[1200px] w-full px-4 py-8">
        <div className="flex flex-col gap-8 items-stretch w-full">
          <h1 className="text-center text-foreground text-xl font-bold tracking-tight py-4 border-b border-border">
            Dashboard
          </h1>
          {isEmpty ? (
            <div className="text-center py-12 w-full backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 rounded-xl">
              <div className="flex flex-col items-center gap-4 px-4">
                <p className="text-lg text-foreground">No letters yet</p>
                <p className="text-sm text-muted-foreground max-w-md">
                  Create a group to start collecting responses, or join one
                  you&apos;ve been invited to.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Button
                    onClick={() => setIsAddGroupOpen(true)}
                    className="gap-1"
                  >
                    <Plus className="h-4 w-4" />
                    Create a group
                  </Button>
                  <Button variant="outline" asChild>
                    <Link to="/groups">View groups</Link>
                  </Button>
                </div>
              </div>
              <AddGroup
                isOpen={isAddGroupOpen}
                onClose={() => setIsAddGroupOpen(false)}
              />
            </div>
          ) : (
            <>
              {recently_completed.length > 0 && (
                <LoopsGrid
                  loops={recently_completed.sort(
                    (a, b) =>
                      new Date(a.send_at).getTime() -
                      new Date(b.send_at).getTime(),
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
                      new Date(a.send_at).getTime() -
                      new Date(b.send_at).getTime(),
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
                      new Date(a.send_at).getTime() -
                      new Date(b.send_at).getTime(),
                  )}
                  heading="Upcoming Issues"
                  subheading="You can add questions to the upcoming issues before they are available"
                  includeGroupName={true}
                  showLoopTypeLabel={true}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
