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
import {
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import GroupInformation from "./GroupInformation"

const invalidate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useRouter: () => ({ invalidate }),
}))

const me = {
  email: "ada@example.com",
  name: "Ada Lovelace",
  api_identifier: "usr_ada",
  admin: false,
  groups: [
    {
      name: "Cloud Seed Group",
      api_identifier: "grp_seed",
    },
  ],
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
  name: "Renamed Seed Group",
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

function GroupInformationHarness() {
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
    qc.setQueryData(readUserMePartiesMeGetQueryKey(), me)
    qc.setQueryData(
      readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: "grp_seed" },
      }),
      group,
    )
    return qc
  })
  return (
    <QueryClientProvider client={queryClient}>
      <GroupInformation groupId="grp_seed" />
      <Toaster />
    </QueryClientProvider>
  )
}

async function enterEditAndRename(name: string) {
  fireEvent.click(screen.getByRole("button", { name: "Edit" }))
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: name },
  })
  fireEvent.click(screen.getByRole("button", { name: "Save" }))
}

afterEach(() => {
  cleanup()
  invalidate.mockReset()
  vi.restoreAllMocks()
})

describe("GroupInformation form", () => {
  it("submits with a finite request timeout", async () => {
    const patch = vi.spyOn(client, "patch").mockResolvedValue({
      data: renamedGroup,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.patch>>)

    render(<GroupInformationHarness />)
    await enterEditAndRename("Renamed Seed Group")

    await waitFor(() => {
      expect(patch).toHaveBeenCalled()
    })

    const call = patch.mock.calls[0]?.[0] as {
      body?: { name?: string }
      timeout?: number
      url?: string
    }
    expect(call.timeout).toBe(20_000)
    expect(call.url).toBe("/parties/group/{group_api_id}")
    expect(call.body).toEqual({ name: "Renamed Seed Group" })

    expect(
      await screen.findByText("Group information updated successfully."),
    ).toBeTruthy()
  })

  it("recovers from a 500 and unlocks Save", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(serverError("rename exploded"))

    render(<GroupInformationHarness />)
    await enterEditAndRename("Broken Name")

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("rename exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Save" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(networkError())

    render(<GroupInformationHarness />)
    await enterEditAndRename("Offline Name")

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
  })
})
