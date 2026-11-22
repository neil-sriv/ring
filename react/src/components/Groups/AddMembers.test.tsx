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

import type { GroupLinked, UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import AddMembers from "./AddMembers"

const me = {
  email: "ada@example.com",
  name: "Ada Lovelace",
  api_identifier: "usr_ada",
  admin: false,
  groups: [],
} satisfies UserLinked

const group = {
  name: "Cloud Seed Group",
  api_identifier: "grp_seed",
  created_at: "2026-11-22T00:00:00.000Z",
  cycle_length: 30,
  members: [
    {
      email: me.email,
      name: me.name,
      api_identifier: me.api_identifier,
      admin: me.admin,
    },
  ],
  admin: {
    email: me.email,
    name: me.name,
    api_identifier: me.api_identifier,
    admin: me.admin,
  },
  default_questions: [],
} satisfies GroupLinked

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

function AddMembersHarness() {
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
      <AddMembers group={group} isOpen={open} onClose={() => setOpen(false)} />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("AddMembers dialog", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: group,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<AddMembersHarness />)

    fireEvent.change(screen.getByLabelText("New Member Emails"), {
      target: { value: "bob@example.com" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { member_emails?: string[] }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body).toEqual({ member_emails: ["bob@example.com"] })

    expect(await screen.findByText("Group updated successfully.")).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("add exploded"))

    render(<AddMembersHarness />)
    fireEvent.change(screen.getByLabelText("New Member Emails"), {
      target: { value: "broken@example.com" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("add exploded")).toBeTruthy()

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

    render(<AddMembersHarness />)
    fireEvent.change(screen.getByLabelText("New Member Emails"), {
      target: { value: "offline@example.com" },
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
