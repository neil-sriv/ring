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

import { client } from "../../client/client.gen"
import AddLetter from "./AddLoop"

const navigate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigate,
}))

const createdLetter = {
  api_identifier: "lttr_created",
  status: "UPCOMING",
  send_at: "2026-12-03T21:00:00.000Z",
  created_at: "2026-11-19T00:00:00.000Z",
  title: null,
  letter_type: "CYCLIC",
  group: {
    api_identifier: "grp_test",
    name: "Test Group",
    created_at: "2026-11-01T00:00:00.000Z",
    cycle_length: 7,
  },
  questions: [],
  responders: [],
  participants: [],
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
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      }),
  )
  return (
    <QueryClientProvider client={queryClient}>
      <AddLetter
        isOpen={open}
        onClose={() => setOpen(false)}
        groupApiId="grp_test"
      />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  navigate.mockReset()
  vi.restoreAllMocks()
})

describe("AddLetter create dialog", () => {
  it("submits a timezone-aware send_at from the datetime-local string", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: createdLetter,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<AddHarness />)

    const sendAt = screen.getByLabelText(/Send at/) as HTMLInputElement
    // Keep as a string end-to-end (no valueAsDate).
    expect(typeof sendAt.value).toBe("string")
    expect(sendAt.value.length).toBeGreaterThan(0)

    fireEvent.change(sendAt, { target: { value: "2026-12-10T21:00" } })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { send_at?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body?.send_at).toMatch(
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$/,
    )
    // Must not submit the bare datetime-local string without offset.
    expect(call.body?.send_at).not.toBe("2026-12-10T21:00")

    expect(
      await screen.findByText("Next letter created successfully."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
    expect(navigate).toHaveBeenCalledWith({
      to: "/loops/$loopId",
      params: { loopId: "lttr_created" },
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("create exploded"))

    render(<AddHarness />)
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
    expect(navigate).not.toHaveBeenCalled()
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<AddHarness />)
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
