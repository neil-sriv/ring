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

import type { GroupLinked } from "../../client"
import { readGroupPartiesGroupGroupApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import GroupLoopSettings from "./GroupLoopSettings"

const invalidate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useRouter: () => ({ invalidate }),
}))

const group = {
  name: "Cloud Seed Group",
  api_identifier: "grp_seed",
  created_at: "2026-11-22T00:00:00.000Z",
  cycle_length: 30,
  min_responder_ratio: 0.5,
  members: [],
  admin: {
    email: "ada@example.com",
    name: "Ada",
    api_identifier: "usr_ada",
    admin: false,
  },
  default_questions: [
    {
      question_text: "What made you smile?",
      api_identifier: "dq_1",
      created_at: "2026-11-22T00:00:00.000Z",
    },
  ],
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

function GroupLoopSettingsHarness() {
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
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
      <GroupLoopSettings groupId="grp_seed" />
      <Toaster />
    </QueryClientProvider>
  )
}

async function enterEditAndBumpCycle() {
  fireEvent.click(screen.getByRole("button", { name: "Edit" }))
  fireEvent.change(screen.getByLabelText("Loop Cycle (days)"), {
    target: { value: "45" },
  })
  fireEvent.click(screen.getByRole("button", { name: "Save" }))
}

afterEach(() => {
  cleanup()
  invalidate.mockReset()
  vi.restoreAllMocks()
})

describe("GroupLoopSettings form", () => {
  it("submits with a finite request timeout on both writes", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: undefined,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)
    const patch = vi.spyOn(client, "patch").mockResolvedValue({
      data: { ...group, cycle_length: 45 },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.patch>>)

    render(<GroupLoopSettingsHarness />)
    await enterEditAndBumpCycle()

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
      expect(patch).toHaveBeenCalled()
    })

    const postCall = post.mock.calls[0]?.[0] as { timeout?: number }
    const patchCall = patch.mock.calls[0]?.[0] as {
      body?: { cycle_length?: number }
      timeout?: number
    }
    expect(postCall.timeout).toBe(20_000)
    expect(patchCall.timeout).toBe(20_000)
    expect(patchCall.body).toEqual({ cycle_length: 45 })

    expect(
      await screen.findByText("Loop settings updated successfully."),
    ).toBeTruthy()
  })

  it("recovers from a 500 on default questions and unlocks Save", async () => {
    vi.spyOn(client, "post").mockRejectedValue(
      serverError("questions exploded"),
    )

    render(<GroupLoopSettingsHarness />)
    await enterEditAndBumpCycle()

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("questions exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Save" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<GroupLoopSettingsHarness />)
    await enterEditAndBumpCycle()

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
