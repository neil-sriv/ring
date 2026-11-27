import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import { AxiosError, type AxiosResponse } from "axios"
import { useState } from "react"
import { Toaster } from "sonner"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { PublicQuestion, UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import LateAnswerQuestion from "./LateAnswerQuestion"

const me = {
  email: "test@example.com",
  name: "Test User",
  api_identifier: "usr_me",
  admin: false,
  groups: [],
} satisfies UserLinked

const unansweredQuestion = {
  question_text: "What made you smile?",
  api_identifier: "qstn_late",
  created_at: "2026-11-01T00:00:00.000Z",
  position: 0,
  added_late: false,
  author: {
    email: "ada@example.com",
    name: "Ada",
    api_identifier: "usr_ada",
    admin: false,
  },
  responses: [],
} satisfies PublicQuestion

function networkError() {
  return new AxiosError("Network Error", AxiosError.ERR_NETWORK)
}

function serverError(detail: string) {
  const error = new AxiosError("Request failed with status code 500")
  error.response = {
    data: { detail },
    status: 500,
    statusText: "Internal Server Error",
    headers: {},
    config: {},
  } as AxiosResponse
  return error
}

function LateAnswerHarness() {
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
    qc.setQueryData(readUserMePartiesMeGetQueryKey(), me)
    return qc
  })
  return (
    <QueryClientProvider client={queryClient}>
      <LateAnswerQuestion question={unansweredQuestion} loopApiId="lttr_sent" />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("LateAnswerQuestion form", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: {
        ...unansweredQuestion,
        responses: [
          {
            response_text: "Sunshine.",
            api_identifier: "resp_1",
            created_at: "2026-11-27T00:00:00.000Z",
            participant: {
              email: me.email,
              name: me.name,
              api_identifier: me.api_identifier,
              admin: false,
            },
            images: [],
          },
        ],
      },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<LateAnswerHarness />)
    fireEvent.change(
      screen.getByPlaceholderText("Add your late answer here..."),
      {
        target: { value: "Sunshine." },
      },
    )
    fireEvent.click(screen.getByRole("button", { name: "Submit Late Answer" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: {
        response_text?: string
        participant_api_identifier?: string
      }
      timeout?: number
      url?: string
    }
    expect(call.timeout).toBe(20_000)
    expect(call.url).toBe(
      "/questions/question/{question_api_id}:upsert_response",
    )
    expect(call.body?.response_text).toBe("Sunshine.")
    expect(call.body?.participant_api_identifier).toBe("usr_me")

    expect(
      await screen.findByText("Your late answer has been submitted."),
    ).toBeTruthy()
  })

  it("recovers from a 500 and unlocks Submit", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("submit exploded"))

    render(<LateAnswerHarness />)
    fireEvent.change(
      screen.getByPlaceholderText("Add your late answer here..."),
      {
        target: { value: "Stuck answer." },
      },
    )
    fireEvent.click(screen.getByRole("button", { name: "Submit Late Answer" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("submit exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (
          screen.getByRole("button", {
            name: "Submit Late Answer",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false)
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<LateAnswerHarness />)
    fireEvent.change(
      screen.getByPlaceholderText("Add your late answer here..."),
      {
        target: { value: "Offline answer." },
      },
    )
    fireEvent.click(screen.getByRole("button", { name: "Submit Late Answer" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(
      screen.getByText("Failed to submit late answer. Please try again."),
    ).toBeTruthy()

    await waitFor(() => {
      expect(
        (
          screen.getByRole("button", {
            name: "Submit Late Answer",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false)
    })
  })
})
