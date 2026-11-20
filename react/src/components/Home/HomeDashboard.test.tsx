import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, render, screen } from "@testing-library/react"
import { type ReactNode, Suspense } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type {
  DashboardLetters,
  DashboardQuestion,
  UserLinked,
} from "../../client"
import {
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { HomeDashboard } from "./HomeDashboard"

vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    className,
  }: {
    children: ReactNode
    className?: string
  }) => <div className={className}>{children}</div>,
}))

const me = {
  email: "ada@example.com",
  name: "Ada Lovelace",
  api_identifier: "usr_ada",
  admin: false,
  groups: [
    {
      name: "Test Group",
      api_identifier: "grp_test",
      created_at: "2026-11-01T00:00:00.000Z",
      cycle_length: 7,
    },
  ],
} satisfies UserLinked

function dashboardQuestion(
  id: string,
  text: string,
  position: number,
  addedLate: boolean,
  responded: string[],
): DashboardQuestion {
  return {
    question_text: text,
    api_identifier: id,
    created_at: "2026-11-01T00:00:00.000Z",
    position,
    added_late: addedLate,
    responded_participant_api_ids: responded,
  }
}

function letters(questions: DashboardQuestion[]): DashboardLetters {
  return {
    upcoming: [],
    recently_completed: [],
    in_progress: [
      {
        api_identifier: "lttr_home",
        status: "IN_PROGRESS",
        send_at: "2026-12-01T00:00:00.000Z",
        created_at: "2026-11-01T00:00:00.000Z",
        title: "Weekly",
        letter_type: "CYCLIC",
        group: {
          api_identifier: "grp_test",
          name: "Test Group",
          created_at: "2026-11-01T00:00:00.000Z",
          cycle_length: 7,
        },
        responders: [me],
        required_responders: 1,
        responder_count: 1,
        questions,
        participant_count: 2,
      },
    ],
  }
}

function renderHome(questions: DashboardQuestion[]) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Number.POSITIVE_INFINITY,
        refetchOnMount: false,
        refetchOnWindowFocus: false,
      },
    },
  })
  queryClient.setQueryData(readUserMePartiesMeGetQueryKey(), me)
  queryClient.setQueryData(
    listDashboardLettersLettersLettersDashboardGetQueryKey(),
    letters(questions),
  )
  return render(
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div>loading</div>}>
        <HomeDashboard />
      </Suspense>
    </QueryClientProvider>,
  )
}

function expectWarningBadge(badge: HTMLElement) {
  expect(badge.className).toContain("text-warning")
  expect(badge.className).toContain("bg-warning/10")
  expect(badge.className).not.toContain("text-info")
  expect(badge.className).not.toContain("bg-info/10")
}

afterEach(() => {
  cleanup()
})

describe("Home waiting list late badge", () => {
  it("shows a Late badge on the question waiting for a reply", async () => {
    renderHome([
      dashboardQuestion("q_done", "Already answered", 1, false, [
        me.api_identifier,
      ]),
      dashboardQuestion("q_late", "What did you forget?", 0, true, []),
    ])

    expect(
      await screen.findByRole("heading", { name: "Waiting on you" }),
    ).toBeTruthy()
    expect(screen.getByText("What did you forget?")).toBeTruthy()
    expect(screen.queryByText("Already answered")).toBeNull()
    expectWarningBadge(screen.getByText("Late"))
    expect(screen.getByText("1 of 2 replied")).toBeTruthy()
    expect(screen.queryByText("Late Answer")).toBeNull()
  })

  it("hides the Late badge when the unanswered question was not added late", async () => {
    renderHome([dashboardQuestion("q_open", "Still open", 0, false, [])])

    expect(
      await screen.findByRole("heading", { name: "Waiting on you" }),
    ).toBeTruthy()
    expect(screen.getByText("Still open")).toBeTruthy()
    expect(screen.queryByText("Late")).toBeNull()
    expect(screen.getByText("1 of 2 replied")).toBeTruthy()
  })

  it("shows one Late badge when the quote and a later question were both added late", async () => {
    renderHome([
      dashboardQuestion("q_late", "What did you forget?", 0, true, []),
      dashboardQuestion("q_also", "And this?", 1, true, []),
    ])

    expect(
      await screen.findByRole("heading", { name: "Waiting on you" }),
    ).toBeTruthy()
    const badges = screen.getAllByText("Late")
    expect(badges).toHaveLength(1)
    expectWarningBadge(badges[0])
    const quote = screen.getByText("What did you forget?")
    expect(quote.closest("blockquote")?.parentElement?.textContent).toContain(
      "Late",
    )
    const answer = screen.getByText(/Answer 2 questions/)
    expect(answer.parentElement?.textContent).not.toContain("Late")
  })

  it("shows the Late badge when a later unanswered question was added late", async () => {
    renderHome([
      dashboardQuestion("q_first", "Earlier question", 0, false, []),
      dashboardQuestion("q_late", "What did you forget?", 1, true, []),
    ])

    expect(
      await screen.findByRole("heading", { name: "Waiting on you" }),
    ).toBeTruthy()
    const quote = screen.getByText("Earlier question")
    expect(quote.closest("blockquote")?.textContent).not.toContain("Late")
    expectWarningBadge(screen.getByText("Late"))
    expect(screen.getByText(/Answer 2 questions/)).toBeTruthy()
  })
})
