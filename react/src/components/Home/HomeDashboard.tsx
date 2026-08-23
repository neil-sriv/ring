import { Button } from "@/components/ui/button"
import { useSuspenseQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Inbox, Plus } from "lucide-react"
import { useState } from "react"
import type { MinimalLetter, Question } from "../../client"
import {
  listDashboardLettersLettersLettersDashboardGetOptions,
  readUserMePartiesMeGetOptions,
} from "../../client/@tanstack/react-query.gen"
import { formatShortDate } from "../../util/loopTime"
import AddGroup from "../Groups/AddGroup"
import { InProgressList } from "./InProgressList"
import { NeedsReplyCard } from "./NeedsReplyCard"
import { PublishedIssueCard } from "./PublishedIssueCard"
import { UpcomingList } from "./UpcomingList"

interface LoopAwaitingReply {
  loop: MinimalLetter
  unansweredQuestions: Question[]
}

function getGreeting(now: Date): string {
  const hour = now.getHours()
  if (hour < 12) {
    return "Good morning"
  }
  if (hour < 18) {
    return "Good afternoon"
  }
  return "Good evening"
}

function getDigest({
  waitingOnYou,
  waitingOnOthersCount,
  upcoming,
  publishedCount,
}: {
  waitingOnYou: LoopAwaitingReply[]
  waitingOnOthersCount: number
  upcoming: MinimalLetter[]
  publishedCount: number
}): string {
  if (waitingOnYou.length > 0) {
    const letterCount = waitingOnYou.length
    const questionCount = waitingOnYou.reduce(
      (sum, entry) => sum + entry.unansweredQuestions.length,
      0,
    )
    const letters = `${letterCount} letter${letterCount !== 1 ? "s" : ""}`
    const verb = letterCount !== 1 ? "are" : "is"
    const questions = `${questionCount} question${
      questionCount !== 1 ? "s" : ""
    }`
    return `${letters} ${verb} waiting on your reply — ${questions} to answer.`
  }
  if (waitingOnOthersCount > 0) {
    return "You're all caught up — the pen is in someone else's hands."
  }
  if (upcoming.length > 0) {
    return `Nothing needs you right now. The next issue sends ${formatShortDate(
      upcoming[0].send_at,
    )}.`
  }
  if (publishedCount > 0) {
    return "All quiet — catch up on the latest issues."
  }
  return "Letters waiting on you and what your groups have been up to."
}

function SectionHeading({
  title,
  count,
  subtitle,
}: {
  title: string
  count?: number
  subtitle?: string
}): JSX.Element {
  return (
    <div>
      <div className="flex items-center gap-2">
        <h2 className="text-base font-semibold">{title}</h2>
        {count !== undefined && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {count}
          </span>
        )}
      </div>
      {subtitle && (
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      )}
    </div>
  )
}

function EmptyDashboard({ hasGroups }: { hasGroups: boolean }): JSX.Element {
  const [isAddGroupOpen, setIsAddGroupOpen] = useState(false)

  return (
    <div className="flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
      <Inbox className="h-8 w-8 text-muted-foreground/60" strokeWidth={1.5} />
      <h3 className="mt-4 font-display text-lg font-medium">No letters yet</h3>
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
  )
}

function bySendAtAsc(a: MinimalLetter, b: MinimalLetter): number {
  return new Date(a.send_at).getTime() - new Date(b.send_at).getTime()
}

export function HomeDashboard(): JSX.Element {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  })
  const currentUser = useSuspenseQuery({
    ...readUserMePartiesMeGetOptions(),
  })
  const userApiId = currentUser.data.api_identifier
  const hasGroups = currentUser.data.groups.length > 0

  const inProgress = [...dashboardLoops.data.in_progress].sort(bySendAtAsc)
  const upcoming = [...dashboardLoops.data.upcoming].sort(bySendAtAsc)
  const published = [...dashboardLoops.data.recently_completed].sort(
    (a, b) => new Date(b.send_at).getTime() - new Date(a.send_at).getTime(),
  )

  const unansweredByLoop = dashboardLoops.data.unanswered_questions
  const waitingOnYou: LoopAwaitingReply[] = []
  const waitingOnOthers: MinimalLetter[] = []
  for (const loop of inProgress) {
    const unansweredQuestions = unansweredByLoop[loop.api_identifier] ?? []
    if (unansweredQuestions.length > 0) {
      waitingOnYou.push({ loop, unansweredQuestions })
    } else {
      waitingOnOthers.push(loop)
    }
  }

  const isEmpty =
    inProgress.length === 0 && upcoming.length === 0 && published.length === 0

  const now = new Date()
  const dateLine = now.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  })
  const firstName = currentUser.data.name.trim().split(/\s+/)[0] || "there"

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <div className="flex w-full flex-col gap-10">
        <header className="border-b pb-6">
          <p className="text-sm text-muted-foreground">{dateLine}</p>
          <h1 className="mt-1 font-display text-2xl font-semibold tracking-tight md:text-3xl">
            {getGreeting(now)}, {firstName}
          </h1>
          {!isEmpty && (
            <p className="mt-2 text-sm text-muted-foreground">
              {getDigest({
                waitingOnYou,
                waitingOnOthersCount: waitingOnOthers.length,
                upcoming,
                publishedCount: published.length,
              })}
            </p>
          )}
        </header>

        {isEmpty ? (
          <EmptyDashboard hasGroups={hasGroups} />
        ) : (
          <>
            {waitingOnYou.length > 0 && (
              <section className="flex flex-col gap-4">
                <SectionHeading
                  title="Waiting on you"
                  count={waitingOnYou.length}
                  subtitle="These letters need your replies before they can send."
                />
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {waitingOnYou.map(({ loop, unansweredQuestions }) => (
                    <NeedsReplyCard
                      key={loop.api_identifier}
                      loop={loop}
                      unansweredQuestions={unansweredQuestions}
                    />
                  ))}
                </div>
              </section>
            )}

            {waitingOnOthers.length > 0 && (
              <section className="flex flex-col gap-4">
                <SectionHeading
                  title="Waiting on others"
                  count={waitingOnOthers.length}
                  subtitle="Still collecting replies from the group."
                />
                <InProgressList loops={waitingOnOthers} userApiId={userApiId} />
              </section>
            )}

            {published.length > 0 && (
              <section className="flex flex-col gap-4">
                <SectionHeading
                  title="Fresh off the press"
                  count={published.length}
                  subtitle="Recently published issues from your groups."
                />
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {published.map((loop) => (
                    <PublishedIssueCard key={loop.api_identifier} loop={loop} />
                  ))}
                </div>
              </section>
            )}

            {upcoming.length > 0 && (
              <section className="flex flex-col gap-4">
                <SectionHeading
                  title="Up next"
                  count={upcoming.length}
                  subtitle="Queued issues — add a question before they open."
                />
                <UpcomingList loops={upcoming} />
              </section>
            )}
          </>
        )}
      </div>
    </div>
  )
}
