import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type {
  LetterStatus,
  PublicQuestion,
  UserLinked,
  UserUnlinked,
} from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import DraftQuestion from "./DraftQuestion"

vi.mock("@tanstack/react-router", () => ({
  useRouter: () => ({ invalidate: vi.fn() }),
}))

function person(name: string, id: string): UserUnlinked {
  return {
    email: `${id}@example.com`,
    name,
    api_identifier: id,
    admin: false,
  }
}

const me = person("Me", "usr_me")
const other = person("Other", "usr_other")

const currentUser = {
  ...me,
  groups: [],
} satisfies UserLinked

function question(
  author: UserUnlinked | null,
  withResponse = false,
): PublicQuestion {
  return {
    question_text: "One good thing?",
    api_identifier: "q_1",
    created_at: "2026-11-01T00:00:00.000Z",
    position: 0,
    added_late: true,
    author,
    responses: withResponse
      ? [
          {
            response_text: "The weather.",
            api_identifier: "resp_1",
            created_at: "2026-11-02T00:00:00.000Z",
            participant: other,
            images: [],
          },
        ]
      : [],
  }
}

function renderQuestion({
  author = me,
  withResponse = false,
  isGroupAdmin = false,
  letterStatus = "IN_PROGRESS",
  readOnly = false,
}: {
  author?: UserUnlinked | null
  withResponse?: boolean
  isGroupAdmin?: boolean
  letterStatus?: LetterStatus
  readOnly?: boolean
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Number.POSITIVE_INFINITY,
        refetchOnMount: false,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
  })
  queryClient.setQueryData(readUserMePartiesMeGetQueryKey(), currentUser)
  return render(
    <QueryClientProvider client={queryClient}>
      <DraftQuestion
        question={question(author, withResponse)}
        loopApiId="lttr_test"
        readOnly={readOnly}
        isGroupAdmin={isGroupAdmin}
        letterStatus={letterStatus}
      />
    </QueryClientProvider>,
  )
}

function deleteButton(): HTMLButtonElement | null {
  return screen.queryByRole("button", {
    name: "Delete",
  }) as HTMLButtonElement | null
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("DraftQuestion delete", () => {
  it("shows Delete to the author of an unanswered question on an in-progress loop", async () => {
    renderQuestion()

    const button = deleteButton()
    expect(button).toBeTruthy()
    fireEvent.click(button as HTMLButtonElement)
    expect(
      await screen.findByRole("heading", { name: "Delete Question" }),
    ).toBeTruthy()
  })

  it("shows Delete to a group admin who did not author the question", () => {
    renderQuestion({ author: other, isGroupAdmin: true })
    expect(deleteButton()).toBeTruthy()
  })

  it("hides Delete from another member", () => {
    renderQuestion({ author: other, isGroupAdmin: false })
    expect(deleteButton()).toBeNull()
  })

  it("hides Delete when the question has a response", () => {
    renderQuestion({ withResponse: true, isGroupAdmin: true })
    expect(deleteButton()).toBeNull()
  })

  it("shows Delete on an upcoming loop while the answer box stays read-only", () => {
    renderQuestion({ letterStatus: "UPCOMING", readOnly: true })

    expect(deleteButton()).toBeTruthy()
    expect(
      (
        screen.getByPlaceholderText(
          "Type your response...",
        ) as HTMLTextAreaElement
      ).disabled,
    ).toBe(true)
  })

  it("keeps the answer box editable on an in-progress loop", () => {
    renderQuestion({ letterStatus: "IN_PROGRESS", readOnly: false })

    expect(
      (
        screen.getByPlaceholderText(
          "Type your response...",
        ) as HTMLTextAreaElement
      ).disabled,
    ).toBe(false)
  })

  it("hides Delete on a sent loop", () => {
    renderQuestion({
      letterStatus: "SENT",
      readOnly: true,
      isGroupAdmin: true,
    })
    expect(deleteButton()).toBeNull()
  })

  it("hides Delete on an upcoming loop once someone has answered", () => {
    renderQuestion({
      letterStatus: "UPCOMING",
      readOnly: true,
      withResponse: true,
      isGroupAdmin: true,
    })
    expect(deleteButton()).toBeNull()
  })
})
