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
import AddUser from "./AddUser"

const createdUser = {
  email: "bob@example.com",
  name: "Bob",
  api_identifier: "usr_bob",
  admin: false,
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

function AddUserHarness() {
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
      <AddUser isOpen={open} onClose={() => setOpen(false)} />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("AddUser dialog", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: createdUser,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<AddUserHarness />)

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "bob@example.com" },
    })
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "Bob" },
    })
    fireEvent.change(screen.getByLabelText("Set Password"), {
      target: { value: "password123" },
    })
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "password123" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { email?: string; name?: string; password?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body?.email).toBe("bob@example.com")
    expect(call.body?.name).toBe("Bob")

    expect(await screen.findByText("User created successfully.")).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("create exploded"))

    render(<AddUserHarness />)
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "broken@example.com" },
    })
    fireEvent.change(screen.getByLabelText("Set Password"), {
      target: { value: "password123" },
    })
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "password123" },
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

    render(<AddUserHarness />)
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "offline@example.com" },
    })
    fireEvent.change(screen.getByLabelText("Set Password"), {
      target: { value: "password123" },
    })
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "password123" },
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
