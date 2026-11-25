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
import ChangePassword from "./ChangePassword"

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

function ChangePasswordHarness() {
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
      <ChangePassword />
      <Toaster />
    </QueryClientProvider>
  )
}

function fillPasswordForm() {
  fireEvent.change(screen.getByLabelText("Current password"), {
    target: { value: "oldpassword123" },
  })
  fireEvent.change(screen.getByLabelText("New password"), {
    target: { value: "newpassword123" },
  })
  fireEvent.change(screen.getByLabelText("Confirm password"), {
    target: { value: "newpassword123" },
  })
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("ChangePassword form", () => {
  it("submits with a finite request timeout", async () => {
    const patch = vi.spyOn(client, "patch").mockResolvedValue({
      data: undefined,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.patch>>)

    render(<ChangePasswordHarness />)
    fillPasswordForm()
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(patch).toHaveBeenCalled()
    })

    const call = patch.mock.calls[0]?.[0] as {
      body?: {
        current_password?: string
        new_password?: string
      }
      timeout?: number
      url?: string
    }
    expect(call.timeout).toBe(20_000)
    expect(call.url).toBe("/parties/me/password")
    expect(call.body?.current_password).toBe("oldpassword123")
    expect(call.body?.new_password).toBe("newpassword123")

    expect(await screen.findByText("Password updated.")).toBeTruthy()
  })

  it("recovers from a 500 and unlocks Save", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(
      serverError("password update exploded"),
    )

    render(<ChangePasswordHarness />)
    fillPasswordForm()
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("password update exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Save" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(networkError())

    render(<ChangePasswordHarness />)
    fillPasswordForm()
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(
      screen.getByText("Something went wrong. Please try again."),
    ).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Save" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
  })
})
