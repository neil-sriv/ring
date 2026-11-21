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

import type { UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import GenerateQuestion from "./GenerateQuestion"

vi.mock("@tanstack/react-router", () => ({
  useRouter: () => ({ invalidate: vi.fn() }),
}))

const currentUser = {
  email: "test@example.com",
  name: "Test User",
  api_identifier: "usr_me",
  admin: false,
  groups: [],
} satisfies UserLinked

const generated = {
  generated_text: "What is one thing you learned this week?",
}

const createdQuestion = {
  question_text: generated.generated_text,
  api_identifier: "qstn_created",
  created_at: "2026-11-21T00:00:00.000Z",
  position: 0,
  added_late: false,
  author: {
    email: currentUser.email,
    name: currentUser.name,
    api_identifier: currentUser.api_identifier,
    admin: false,
  },
  responses: [],
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

function GenerateHarness() {
  const [open, setOpen] = useState(true)
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
    qc.setQueryData(readUserMePartiesMeGetQueryKey(), currentUser)
    return qc
  })
  return (
    <QueryClientProvider client={queryClient}>
      <GenerateQuestion
        isOpen={open}
        onClose={() => setOpen(false)}
        loopApiId="lttr_test"
      />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("GenerateQuestion dialog", () => {
  it("generates with a 60s timeout then saves with a 20s timeout", async () => {
    const post = vi
      .spyOn(client, "post")
      .mockResolvedValueOnce({
        data: generated,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      } as Awaited<ReturnType<typeof client.post>>)
      .mockResolvedValueOnce({
        data: createdQuestion,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      } as Awaited<ReturnType<typeof client.post>>)

    render(<GenerateHarness />)

    fireEvent.change(screen.getByLabelText("Prompt"), {
      target: { value: "Ask about learning" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Generate" }))

    expect(
      await screen.findByText("Question generated successfully."),
    ).toBeTruthy()
    expect(await screen.findByText(generated.generated_text)).toBeTruthy()

    const generateCall = post.mock.calls[0]?.[0] as {
      body?: { prompt?: string }
      timeout?: number
    }
    expect(generateCall.timeout).toBe(60_000)
    expect(generateCall.body?.prompt).toBe("Ask about learning")

    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalledTimes(2)
    })

    const saveCall = post.mock.calls[1]?.[0] as {
      body?: { question_text?: string }
      timeout?: number
    }
    expect(saveCall.timeout).toBe(20_000)
    expect(saveCall.body?.question_text).toBe(generated.generated_text)

    expect(
      await screen.findByText("New question created successfully."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a generate 500 so the dialog can close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("llm exploded"))

    render(<GenerateHarness />)
    fireEvent.change(screen.getByLabelText("Prompt"), {
      target: { value: "Anything" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Generate" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("llm exploded")).toBeTruthy()

    const generate = screen.getByRole("button", { name: "Generate" })
    await waitFor(() => {
      expect((generate as HTMLButtonElement).disabled).toBe(false)
    })

    fireEvent.click(screen.getByRole("button", { name: "Close" }))
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })
})
