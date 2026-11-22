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
import EditGroup from "./EditGroup"

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

const renamedGroup = {
  ...group,
  name: "Renamed Group",
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

function EditHarness() {
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
      <EditGroup group={group} isOpen={open} onClose={() => setOpen(false)} />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("EditGroup dialog", () => {
  it("submits with a finite request timeout", async () => {
    const patch = vi.spyOn(client, "patch").mockResolvedValue({
      data: renamedGroup,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.patch>>)

    render(<EditHarness />)

    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Renamed Group" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(patch).toHaveBeenCalled()
    })

    const call = patch.mock.calls[0]?.[0] as {
      body?: { name?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body).toEqual({ name: "Renamed Group" })

    expect(await screen.findByText("Group updated successfully.")).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull()
    })
  })

  it("recovers from a 500 and lets the dialog close", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(serverError("rename exploded"))

    render(<EditHarness />)
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Broken Name" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("rename exploded")).toBeTruthy()

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
    vi.spyOn(client, "patch").mockRejectedValue(networkError())

    render(<EditHarness />)
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Offline Name" },
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
