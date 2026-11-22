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

import type { UserLinked, UserUnlinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import RemoveMemberConfirmation from "./RemoveMemberConfirmation"

const invalidate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useRouter: () => ({ invalidate }),
}))

const me = {
  email: "ada@example.com",
  name: "Ada Lovelace",
  api_identifier: "usr_ada",
  admin: false,
  groups: [],
} satisfies UserLinked

const member = {
  email: "bob@example.com",
  name: "Bob Member",
  api_identifier: "usr_bob",
  admin: false,
} satisfies UserUnlinked

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

function RemoveHarness() {
  const [open, setOpen] = useState(true)
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    qc.setQueryData(readUserMePartiesMeGetQueryKey(), me)
    return qc
  })
  return (
    <QueryClientProvider client={queryClient}>
      <RemoveMemberConfirmation
        groupId="grp_seed"
        member={member}
        isOpen={open}
        onClose={() => setOpen(false)}
      />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  invalidate.mockReset()
  vi.restoreAllMocks()
})

describe("RemoveMemberConfirmation dialog", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: {},
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<RemoveHarness />)

    fireEvent.click(screen.getByRole("button", { name: "Remove" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      timeout?: number
      url?: string
    }
    expect(call.timeout).toBe(20_000)

    expect(
      await screen.findByText("Bob Member was removed from the group."),
    ).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).toBeNull()
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("remove exploded"))

    render(<RemoveHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Remove" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("remove exploded")).toBeTruthy()

    const remove = screen.getByRole("button", { name: "Remove" })
    await waitFor(() => {
      expect((remove as HTMLButtonElement).disabled).toBe(false)
    })

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).toBeNull()
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<RemoveHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Remove" }))

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
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).toBeNull()
    })
  })
})
