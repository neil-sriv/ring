import { Button } from "@/components/ui/button"
import { useSuspenseQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Inbox, Plus } from "lucide-react"
import { useState } from "react"
import {
  listDashboardLettersLettersLettersDashboardGetOptions,
  readUserMePartiesMeGetOptions,
} from "../../client/@tanstack/react-query.gen"
import AddGroup from "../Groups/AddGroup"
import { LoopsGrid } from "../Loops/LoopsGrid"

export function HomeDashboard() {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  })
  const currentUser = useSuspenseQuery({
    ...readUserMePartiesMeGetOptions(),
  })
  const recently_completed = dashboardLoops.data.recently_completed
  const in_progress = dashboardLoops.data.in_progress
  const upcoming = dashboardLoops.data.upcoming
  const hasGroups = currentUser.data.groups.length > 0
  const [isAddGroupOpen, setIsAddGroupOpen] = useState(false)

  const isEmpty =
    recently_completed.length === 0 &&
    in_progress.length === 0 &&
    upcoming.length === 0

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <div className="flex w-full flex-col gap-10">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
            Home
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Letters waiting on you and what your groups have been up to.
          </p>
        </div>
        {isEmpty ? (
          <div className="flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
            <Inbox
              className="h-8 w-8 text-muted-foreground/60"
              strokeWidth={1.5}
            />
            <h3 className="mt-4 font-display text-lg font-medium">
              No letters yet
            </h3>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              {hasGroups
                ? "Start a letter loop from one of your groups to collect responses."
                : "Create a group to start collecting responses, or join one you've been invited to."}
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              {!hasGroups && (
                <Button onClick={() => setIsAddGroupOpen(true)}>
                  <Plus className="h-4 w-4" />
                  Create a group
                </Button>
              )}
              <Button variant="outline" asChild>
                <Link to="/groups">View groups</Link>
              </Button>
            </div>
            {!hasGroups && (
              <AddGroup
                isOpen={isAddGroupOpen}
                onClose={() => setIsAddGroupOpen(false)}
              />
            )}
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
                subheading="Add your response now."
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
  )
}
