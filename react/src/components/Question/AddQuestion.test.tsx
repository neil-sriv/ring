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
import AddQuestion from "./AddQuestion"

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

const createdQuestion = {
  question_text: "What made you smile?",
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

function AddHarness() {
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
      <AddQuestion
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

describe("AddQuestion dialog", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: createdQuestion,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<AddHarness />)

    fireEvent.change(screen.getByLabelText("Question"), {
      target: { value: "What made you smile?" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { question_text?: string; author_api_id?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body?.question_text).toBe("What made you smile?")
    expect(call.body?.author_api_id).toBe("usr_me")

    expect(
      await screen.findByText("New question created successfully."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("create exploded"))

    render(<AddHarness />)
    fireEvent.change(screen.getByLabelText("Question"), {
      target: { value: "Stuck question?" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("create exploded")).toBeTruthy()

    const save = screen.getByRole("button", { name: "Save" })
    await waitFor(() => {
      expect((save as HTMLButtonElement).disabled).toBe(false)
    })

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<AddHarness />)
    fireEvent.change(screen.getByLabelText("Question"), {
      target: { value: "Network flaky?" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(
      screen.getByText("Something went wrong. Please try again."),
    ).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Cancel" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
    fireEvent.click(screen.getByRole("button", { name: "Close" }))
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })
})
