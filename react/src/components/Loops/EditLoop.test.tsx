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

import type { PublicLetter } from "../../client"
import { client } from "../../client/client.gen"
import EditLetter from "./EditLoop"

const loop = {
  api_identifier: "lttr_test",
  status: "UPCOMING",
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
  questions: [],
  responders: [],
  participants: [],
} satisfies PublicLetter

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

function EditHarness() {
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
      <EditLetter isOpen={open} onClose={() => setOpen(false)} loop={loop} />
      <Toaster />
    </QueryClientProvider>
  )
}

async function saveTitle(nextTitle: string) {
  fireEvent.change(screen.getByLabelText("Title"), {
    target: { value: nextTitle },
  })
  fireEvent.click(screen.getByRole("button", { name: "Save" }))
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("EditLetter save failures", () => {
  it("recovers from a 500 and lets the dialog close", async () => {
    const post = vi
      .spyOn(client, "post")
      .mockRejectedValue(serverError("edit exploded"))

    render(<EditHarness />)
    await saveTitle("Renamed")

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("edit exploded")).toBeTruthy()
    expect(post).toHaveBeenCalledWith(
      expect.objectContaining({ timeout: 20_000 }),
    )

    const save = screen.getByRole("button", { name: "Save" })
    await waitFor(() => {
      expect((save as HTMLButtonElement).disabled).toBe(false)
    })
    expect(save.querySelector("svg")).toBeNull()

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<EditHarness />)
    await saveTitle("Renamed")

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

  it("still closes after a successful save", async () => {
    vi.spyOn(client, "post").mockResolvedValue({
      data: { ...loop, title: "Renamed" },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<EditHarness />)
    await saveTitle("Renamed")

    expect(await screen.findByText("Letter updated successfully.")).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })
})
