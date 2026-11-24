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
import { client } from "../../client/client.gen"
import ImpersonateUser from "./ImpersonateUser"

const navigate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigate,
}))

const targetUser = {
  email: "bob@example.com",
  name: "Bob",
  api_identifier: "usr_bob",
  admin: false,
  groups: [],
} satisfies UserLinked

const impersonatedMe = {
  ...targetUser,
  groups: [],
} satisfies UserLinked

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

function ImpersonateUserHarness() {
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
      <ImpersonateUser
        user={targetUser}
        isOpen={open}
        onClose={() => setOpen(false)}
      />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  navigate.mockReset()
  vi.restoreAllMocks()
  localStorage.clear()
})

describe("ImpersonateUser dialog", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: { access_token: "impersonation-token", token_type: "bearer" },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)
    const get = vi.spyOn(client, "get").mockResolvedValue({
      data: impersonatedMe,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.get>>)

    render(<ImpersonateUserHarness />)

    fireEvent.click(screen.getByRole("button", { name: "Impersonate" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      query?: { user_api_id?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.query).toEqual({ user_api_id: "usr_bob" })

    expect(
      await screen.findByText("Impersonated user successfully."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
    expect(localStorage.getItem("access_token")).toBe("impersonation-token")
    await waitFor(() => {
      expect(get).toHaveBeenCalled()
      expect(navigate).toHaveBeenCalledWith({ to: "/" })
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(
      serverError("impersonate exploded"),
    )

    render(<ImpersonateUserHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Impersonate" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("impersonate exploded")).toBeTruthy()

    const submit = screen.getByRole("button", { name: "Impersonate" })
    await waitFor(() => {
      expect((submit as HTMLButtonElement).disabled).toBe(false)
    })

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
    expect(navigate).not.toHaveBeenCalled()
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<ImpersonateUserHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Impersonate" }))

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
    expect(navigate).not.toHaveBeenCalled()
  })
})
