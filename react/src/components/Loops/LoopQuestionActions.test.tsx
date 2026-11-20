import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import { AxiosError, type AxiosResponse } from "axios"
import { Toaster } from "sonner"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { PublicLetter, UserLinked, UserUnlinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import { LATE_QUESTION_CUTOFF_REASON } from "../../util/lateQuestion"
import { LoopQuestionActions } from "./LoopQuestionActions"

vi.mock("@tanstack/react-router", () => ({
  useRouter: () => ({ invalidate: vi.fn() }),
}))

const HOUR_MS = 60 * 60 * 1000

function person(name: string, id: string): UserUnlinked {
  return {
    email: `${id}@example.com`,
    name,
    api_identifier: id,
    admin: false,
  }
}

const ada = person("Ada", "usr_ada")
const bo = person("Bo", "usr_bo")
const cy = person("Cy", "usr_cy")
const former = person("Former", "usr_former")

const currentUser = {
  email: ada.email,
  name: ada.name,
  api_identifier: ada.api_identifier,
  admin: false,
  groups: [],
} satisfies UserLinked

function letter(overrides: Partial<PublicLetter> = {}): PublicLetter {
  return {
    api_identifier: "lttr_test",
    status: "IN_PROGRESS",
    send_at: new Date(Date.now() + 10 * 24 * HOUR_MS).toISOString(),
    created_at: "2026-11-01T00:00:00.000Z",
    title: "Weekly",
    letter_type: "CYCLIC",
    group: {
      api_identifier: "grp_test",
      name: "Test Group",
      created_at: "2026-11-01T00:00:00.000Z",
      cycle_length: 7,
    },
    questions: [],
    responders: [bo, ada, former],
    participants: [ada, bo, cy],
    ...overrides,
  }
}

function serverError(detail: string) {
  const error = new AxiosError("Request failed with status code 400")
  error.response = {
    data: { detail },
    status: 400,
    statusText: "Bad Request",
    headers: {},
    config: {},
  } as AxiosResponse
  return error
}

function renderActions(loop: PublicLetter) {
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
      <LoopQuestionActions loop={loop} />
      <Toaster />
    </QueryClientProvider>,
  )
}

function openComposer() {
  fireEvent.click(screen.getByRole("button", { name: "Add a late question" }))
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("LoopQuestionActions", () => {
  it("shows the late-question banner and who already replied on an in-progress loop", () => {
    renderActions(letter())

    expect(screen.getByText("Forgot to ask something?")).toBeTruthy()
    expect(
      screen.queryByRole("button", { name: "Add new question" }),
    ).toBeNull()
    expect(
      screen.queryByRole("button", {
        name: "Ask ChatGPT to generate a question.",
      }),
    ).toBeNull()
    expect(
      screen.queryByRole("textbox", { name: "What should everyone answer?" }),
    ).toBeNull()

    openComposer()

    expect(
      screen.getByRole("textbox", { name: "What should everyone answer?" }),
    ).toBeTruthy()
    expect(
      screen.getByText(
        "2 of 3 people have already replied: Ada and Bo. They'll be told about this question. It will appear at the top of the letter.",
      ),
    ).toBeTruthy()
  })

  it("says when nobody has replied yet", () => {
    renderActions(letter({ responders: [], participants: [ada, bo] }))
    openComposer()

    expect(
      screen.getByText(
        "0 of 2 people have already replied. It will appear at the top of the letter.",
      ),
    ).toBeTruthy()
    expect(screen.queryByText(/They'll be told/)).toBeNull()
  })

  it("keeps the normal add buttons on an upcoming loop", async () => {
    renderActions(letter({ status: "UPCOMING" }))

    expect(screen.queryByText("Forgot to ask something?")).toBeNull()
    expect(
      screen.getByRole("button", {
        name: "Ask ChatGPT to generate a question.",
      }),
    ).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: "Add new question" }))
    expect(
      await screen.findByRole("heading", { name: "Add new question" }),
    ).toBeTruthy()
  })

  it("shows no add UI on a sent loop", () => {
    renderActions(letter({ status: "SENT" }))

    expect(screen.queryByText("Forgot to ask something?")).toBeNull()
    expect(
      screen.queryByRole("button", { name: "Add new question" }),
    ).toBeNull()
    expect(
      screen.queryByRole("button", {
        name: "Ask ChatGPT to generate a question.",
      }),
    ).toBeNull()
    expect(
      screen.queryByRole("button", { name: "Add a late question" }),
    ).toBeNull()
  })

  it("disables the composer inside the 24 hour cutoff", () => {
    renderActions(
      letter({ send_at: new Date(Date.now() + 23 * HOUR_MS).toISOString() }),
    )

    const openButton = screen.getByRole("button", {
      name: "Add a late question",
    }) as HTMLButtonElement
    expect(openButton.disabled).toBe(true)
    const textarea = screen.getByRole("textbox", {
      name: "What should everyone answer?",
    }) as HTMLTextAreaElement
    expect(textarea.disabled).toBe(true)
    const submit = screen.getByRole("button", {
      name: "Add Late Question",
    }) as HTMLButtonElement
    expect(submit.disabled).toBe(true)
    expect(
      screen.getAllByText(LATE_QUESTION_CUTOFF_REASON).length,
    ).toBeGreaterThan(0)
  })

  it("disables the composer when send time is exactly 24 hours away", () => {
    renderActions(
      letter({ send_at: new Date(Date.now() + 24 * HOUR_MS).toISOString() }),
    )

    expect(
      (
        screen.getByRole("button", {
          name: "Add a late question",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true)
  })

  it("keeps the composer available just outside the cutoff and when send_at is missing", () => {
    const { unmount } = renderActions(
      letter({
        send_at: new Date(Date.now() + 24 * HOUR_MS + 60_000).toISOString(),
      }),
    )
    expect(
      (
        screen.getByRole("button", {
          name: "Add a late question",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false)
    expect(screen.queryByText(LATE_QUESTION_CUTOFF_REASON)).toBeNull()
    unmount()

    renderActions(letter({ send_at: "" }))
    expect(
      (
        screen.getByRole("button", {
          name: "Add a late question",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false)
  })

  it("toasts the server's 400 message when a late add is rejected", async () => {
    vi.spyOn(client, "post").mockRejectedValue(
      serverError(LATE_QUESTION_CUTOFF_REASON),
    )
    renderActions(letter())
    openComposer()

    fireEvent.change(
      screen.getByRole("textbox", { name: "What should everyone answer?" }),
      { target: { value: "What did we miss?" } },
    )
    fireEvent.click(screen.getByRole("button", { name: "Add Late Question" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText(LATE_QUESTION_CUTOFF_REASON)).toBeTruthy()
    expect(
      screen.getByRole("textbox", { name: "What should everyone answer?" }),
    ).toBeTruthy()
  })

  it("adds a late question for the signed-in member", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: letter(),
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    renderActions(letter())
    openComposer()
    fireEvent.change(
      screen.getByRole("textbox", { name: "What should everyone answer?" }),
      { target: { value: "  What did we miss?  " } },
    )
    fireEvent.click(screen.getByRole("button", { name: "Add Late Question" }))

    expect(
      await screen.findByText("Your late question has been added."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(post).toHaveBeenCalledWith(
        expect.objectContaining({
          body: {
            question_text: "What did we miss?",
            // Caller's own id. Omitted or another member's id is not sent.
            author_api_id: ada.api_identifier,
          },
        }),
      )
    })
    expect(
      screen.queryByRole("textbox", { name: "What should everyone answer?" }),
    ).toBeNull()
  })
})
