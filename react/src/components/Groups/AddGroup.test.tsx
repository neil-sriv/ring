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
import AddGroup from "./AddGroup"

const navigate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigate,
}))

const me = {
  email: "ada@example.com",
  name: "Ada Lovelace",
  api_identifier: "usr_ada",
  admin: false,
  groups: [],
} satisfies UserLinked

const createdGroup = {
  name: "Fresh Group",
  api_identifier: "grp_created",
  created_at: "2026-11-20T00:00:00.000Z",
  cycle_length: 30,
  members: [
    {
      email: me.email,
      name: me.name,
      api_identifier: me.api_identifier,
    },
  ],
  admin: {
    email: me.email,
    name: me.name,
    api_identifier: me.api_identifier,
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

function AddHarness() {
  const [open, setOpen] = useState(true)
  const [queryClient] = useState(() => {
    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    client.setQueryData(readUserMePartiesMeGetQueryKey(), me)
    return client
  })
  return (
    <QueryClientProvider client={queryClient}>
      <AddGroup isOpen={open} onClose={() => setOpen(false)} />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  navigate.mockReset()
  vi.restoreAllMocks()
})

describe("AddGroup create dialog", () => {
  it("navigates to the new group's loops page after create", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: createdGroup,
      status: 201,
      statusText: "Created",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<AddHarness />)

    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Fresh Group" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { name?: string; admin_api_identifier?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body).toEqual({
      name: "Fresh Group",
      admin_api_identifier: "usr_ada",
    })

    expect(await screen.findByText("Group created successfully.")).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
    expect(navigate).toHaveBeenCalledWith({
      to: "/groups/$groupId/loops",
      params: { groupId: "grp_created" },
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("create exploded"))

    render(<AddHarness />)
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Broken Group" },
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
    expect(navigate).not.toHaveBeenCalled()
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<AddHarness />)
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Offline Group" },
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
    expect(navigate).not.toHaveBeenCalled()
  })
})
