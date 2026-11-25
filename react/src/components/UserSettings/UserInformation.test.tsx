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
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import UserInformation from "./UserInformation"

vi.mock("@/components/Common/PushOffer", () => ({
  PushNotificationSettings: () => null,
}))

const me = {
  email: "test@example.com",
  name: "Test User",
  api_identifier: "usr_test",
  admin: false,
  groups: [],
} satisfies UserLinked

const updatedMe = {
  ...me,
  name: "Updated User",
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

function UserInformationHarness() {
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
      <UserInformation />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("UserInformation form", () => {
  it("submits with a finite request timeout", async () => {
    const patch = vi.spyOn(client, "patch").mockResolvedValue({
      data: updatedMe,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.patch>>)
    // After save, onSettled refetches /me.
    vi.spyOn(client, "get").mockResolvedValue({
      data: updatedMe,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.get>>)

    render(<UserInformationHarness />)

    fireEvent.click(screen.getByRole("button", { name: "Edit" }))
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "Updated User" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
      expect(patch).toHaveBeenCalled()
    })

    const call = patch.mock.calls[0]?.[0] as {
      body?: { email?: string; name?: string }
      timeout?: number
      url?: string
    }
    expect(call.timeout).toBe(20_000)
    expect(call.url).toBe("/parties/me")
    expect(call.body).toEqual({
      email: "test@example.com",
      name: "Updated User",
    })

    expect(await screen.findByText("User updated successfully.")).toBeTruthy()
  })

  it("recovers from a 500 and unlocks Cancel", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(serverError("update exploded"))

    render(<UserInformationHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Edit" }))
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "Broken" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("update exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (screen.getByRole("button", { name: "Cancel" }) as HTMLButtonElement)
          .disabled,
      ).toBe(false)
    })
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }))
    expect(screen.getByRole("button", { name: "Edit" })).toBeTruthy()
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "patch").mockRejectedValue(networkError())

    render(<UserInformationHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Edit" }))
    fireEvent.change(screen.getByLabelText("Full name"), {
      target: { value: "Offline" },
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
  })
})
