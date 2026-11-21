import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react"
import { AxiosError, type AxiosResponse } from "axios"
import { Toaster } from "sonner"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { PublicLetter, PublicQuestion, UserUnlinked } from "../../client"
import {
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listLettersLettersLettersGetQueryKey,
  readLetterLettersLetterLetterApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import { SendLetterNow } from "./SendLetterNow"

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
const dee = person("Dee", "usr_dee")

function question(respondents: UserUnlinked[]): PublicQuestion {
  return {
    question_text: "How was your week?",
    api_identifier: "q_1",
    created_at: "2026-11-01T00:00:00.000Z",
    position: 0,
    added_late: false,
    author: ada,
    responses: respondents.map((respondent, index) => ({
      response_text: "Answered.",
      api_identifier: `resp_${index}`,
      created_at: "2026-11-02T00:00:00.000Z",
      participant: respondent,
      images: [],
    })),
  }
}

const loop: PublicLetter = {
  api_identifier: "lttr_test",
  status: "IN_PROGRESS",
  send_at: "2026-12-01T20:00:00.000Z",
  created_at: "2026-11-01T00:00:00.000Z",
  title: "Weekly",
  letter_type: "CYCLIC",
  group: {
    api_identifier: "grp_test",
    name: "Test Group",
    created_at: "2026-11-01T00:00:00.000Z",
    cycle_length: 7,
  },
  questions: [question([ada, bo, cy])],
  responders: [ada, bo],
  participants: [ada, bo, cy, dee],
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

function postResult(data: PublicLetter): AxiosResponse {
  return {
    data,
    status: 200,
    statusText: "OK",
    headers: {},
    config: {},
  } as AxiosResponse
}

function renderSend({
  letter = loop,
  isGroupAdmin = true,
}: {
  letter?: PublicLetter
  isGroupAdmin?: boolean
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  const invalidate = vi.spyOn(queryClient, "invalidateQueries")
  const letterKey = readLetterLettersLetterLetterApiIdGetQueryKey({
    path: { letter_api_id: letter.api_identifier },
  })
  queryClient.setQueryData(letterKey, letter)
  render(
    <QueryClientProvider client={queryClient}>
      <SendLetterNow loop={letter} isGroupAdmin={isGroupAdmin} />
      <Toaster />
    </QueryClientProvider>,
  )
  return { queryClient, invalidate, letterKey }
}

function openDialog() {
  fireEvent.click(screen.getByRole("button", { name: "Send now" }))
  return screen.getByRole("alertdialog")
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("SendLetterNow", () => {
  it("shows Send now to a group admin on an in-progress loop", () => {
    renderSend()
    expect(screen.getByRole("button", { name: "Send now" })).toBeTruthy()
  })

  it("hides Send now from a member and from loops that are not in progress", () => {
    const { unmount } = render(
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: { queries: { retry: false } },
          })
        }
      >
        <SendLetterNow loop={loop} isGroupAdmin={false} />
      </QueryClientProvider>,
    )
    expect(screen.queryByRole("button", { name: "Send now" })).toBeNull()
    unmount()

    renderSend({ letter: { ...loop, status: "UPCOMING" } })
    expect(screen.queryByRole("button", { name: "Send now" })).toBeNull()
    cleanup()

    renderSend({ letter: { ...loop, status: "SENT" } })
    expect(screen.queryByRole("button", { name: "Send now" })).toBeNull()
  })

  it("states how many members the reply tracker counts as responded", () => {
    renderSend()
    const dialog = openDialog()
    expect(dialog.textContent).toContain(
      "3 of 4 members have responded so far.",
    )
    expect(dialog.textContent).toContain("The next loop will be scheduled.")
  })

  it("omits the next-loop note on a one-off loop", () => {
    renderSend({ letter: { ...loop, letter_type: "ADHOC" } })
    const dialog = openDialog()
    expect(dialog.textContent).toContain(
      "3 of 4 members have responded so far.",
    )
    expect(dialog.textContent).not.toContain("next loop")
  })

  it("calls send_now once and marks the loop sent", async () => {
    const post = vi
      .spyOn(client, "post")
      .mockResolvedValue(postResult({ ...loop, status: "SENT" }))
    const { queryClient, invalidate, letterKey } = renderSend()
    const dialog = openDialog()
    fireEvent.click(within(dialog).getByRole("button", { name: "Send now" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalledTimes(1)
    })
    const request = post.mock.calls[0]?.[0] as {
      url?: string
      body?: unknown
      path?: { letter_api_id?: string }
    }
    expect(request.url).toBe("/letters/letter/{letter_api_id}:send_now")
    expect(request.body).toBeUndefined()
    expect(request.path).toEqual({ letter_api_id: "lttr_test" })

    expect(await screen.findByText("Loop sent.")).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).toBeNull()
    })
    expect(queryClient.getQueryData<PublicLetter>(letterKey)?.status).toBe(
      "SENT",
    )
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
        path: { letter_api_id: "lttr_test" },
      }),
    })
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: listLettersLettersLettersGetQueryKey({
        query: { group_api_id: "grp_test" },
      }),
    })
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
    })
  })

  it("disables confirm while the send is in flight", async () => {
    let resolvePost: (value: AxiosResponse) => void = () => {}
    const post = vi.spyOn(client, "post").mockImplementation(
      () =>
        new Promise<AxiosResponse>((resolve) => {
          resolvePost = resolve
        }),
    )
    renderSend()
    const dialog = openDialog()
    const confirm = within(dialog).getByRole("button", { name: "Send now" })
    fireEvent.click(confirm)

    await waitFor(() => {
      expect((confirm as HTMLButtonElement).disabled).toBe(true)
    })
    fireEvent.click(confirm)
    expect(post).toHaveBeenCalledTimes(1)

    resolvePost(postResult({ ...loop, status: "SENT" }))
    expect(await screen.findByText("Loop sent.")).toBeTruthy()
  })

  it("shows the API error and leaves the loop in progress", async () => {
    vi.spyOn(client, "post").mockRejectedValue(
      serverError("Letter email was not accepted"),
    )
    const { queryClient, letterKey } = renderSend()
    const dialog = openDialog()
    fireEvent.click(within(dialog).getByRole("button", { name: "Send now" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("Letter email was not accepted")).toBeTruthy()
    expect(queryClient.getQueryData<PublicLetter>(letterKey)?.status).toBe(
      "IN_PROGRESS",
    )

    await waitFor(() => {
      expect(
        (
          within(screen.getByRole("alertdialog")).getByRole("button", {
            name: "Send now",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false)
    })
  })
})
