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
import DeleteConfirmation from "./DeleteConfirmation"

const logout = vi.fn()

vi.mock("../../hooks/useAuth", () => ({
  default: () => ({ logout }),
}))

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

function DeleteConfirmationHarness() {
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
      <DeleteConfirmation isOpen={open} onClose={() => setOpen(false)} />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  logout.mockReset()
  vi.restoreAllMocks()
})

describe("DeleteConfirmation dialog", () => {
  it("submits with a finite request timeout", async () => {
    const del = vi.spyOn(client, "delete").mockResolvedValue({
      data: undefined,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.delete>>)

    render(<DeleteConfirmationHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }))

    await waitFor(() => {
      expect(del).toHaveBeenCalled()
    })

    const call = del.mock.calls[0]?.[0] as {
      timeout?: number
      url?: string
    }
    expect(call.timeout).toBe(20_000)
    expect(call.url).toBe("/parties/me")

    expect(
      await screen.findByText("Your account has been successfully deleted."),
    ).toBeTruthy()
    expect(logout).toHaveBeenCalled()
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).toBeNull()
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "delete").mockRejectedValue(serverError("delete exploded"))

    render(<DeleteConfirmationHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("delete exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Cancel" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).toBeNull()
    })
    expect(logout).not.toHaveBeenCalled()
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "delete").mockRejectedValue(networkError())

    render(<DeleteConfirmationHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }))

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
    expect(logout).not.toHaveBeenCalled()
  })
})
