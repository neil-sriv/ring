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
import AddAdhocLoop from "./AddAdhocLoop"

const navigate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigate,
}))

const createdLetter = {
  api_identifier: "lttr_adhoc",
  status: "UPCOMING",
  send_at: "2026-12-03T21:00:00.000Z",
  created_at: "2026-11-19T00:00:00.000Z",
  title: "One-off",
  letter_type: "ADHOC",
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
      <AddAdhocLoop
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

describe("AddAdhocLoop create dialog", () => {
  it("submits a timezone-aware send_at and navigates on success", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: createdLetter,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<AddHarness />)

    fireEvent.change(screen.getByLabelText("Title (Optional)"), {
      target: { value: "One-off" },
    })
    fireEvent.change(screen.getByLabelText(/Send at/), {
      target: { value: "2026-12-10T21:00" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Create Adhoc Loop" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { send_at?: string; title?: string | null }
      path?: { letter_type?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.path?.letter_type).toBe("ADHOC")
    expect(call.body?.title).toBe("One-off")
    expect(call.body?.send_at).toMatch(
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$/,
    )
    expect(call.body?.send_at).not.toBe("2026-12-10T21:00")

    expect(
      await screen.findByText("Adhoc loop created successfully."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
    expect(navigate).toHaveBeenCalledWith({
      to: "/loops/$loopId",
      params: { loopId: "lttr_adhoc" },
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("adhoc exploded"))

    render(<AddHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Create Adhoc Loop" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("adhoc exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (
          screen.getByRole("button", {
            name: "Create Adhoc Loop",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false)
    })

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
    expect(navigate).not.toHaveBeenCalled()
  })
})
