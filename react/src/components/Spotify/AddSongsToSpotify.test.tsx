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

import type { SpotifyLibrarySaveResponse, SpotifyStatus } from "../../client"
import { readSpotifyStatusSpotifyStatusGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import { AddSongsToSpotify } from "./AddSongsToSpotify"

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
}))

const statusLinked = {
  configured: true,
  linked: true,
} satisfies SpotifyStatus

const saved = {
  saved_count: 3,
} satisfies SpotifyLibrarySaveResponse

function timeoutError() {
  return new AxiosError("timeout of 60000ms exceeded", AxiosError.ECONNABORTED)
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

function SaveHarness() {
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
    qc.setQueryData(readSpotifyStatusSpotifyStatusGetQueryKey(), statusLinked)
    return qc
  })
  return (
    <QueryClientProvider client={queryClient}>
      <AddSongsToSpotify loopApiId="lttr_seed" />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("AddSongsToSpotify", () => {
  it("saves with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: saved,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<SaveHarness />)

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Add these songs to your Spotify account",
      }),
    )

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as { timeout?: number }
    expect(call.timeout).toBe(60_000)

    expect(
      await screen.findByText("Saved 3 songs to your Spotify library."),
    ).toBeTruthy()
  })

  it("toasts a timeout message and unlocks the button", async () => {
    vi.spyOn(client, "post").mockRejectedValue(timeoutError())

    render(<SaveHarness />)

    const button = await screen.findByRole("button", {
      name: "Add these songs to your Spotify account",
    })
    fireEvent.click(button)

    expect(
      await screen.findByText("Spotify request timed out. Please try again."),
    ).toBeTruthy()

    await waitFor(() => {
      expect((button as HTMLButtonElement).disabled).toBe(false)
    })
  })

  it("toasts API errors and unlocks the button", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("library failed"))

    render(<SaveHarness />)

    const button = await screen.findByRole("button", {
      name: "Add these songs to your Spotify account",
    })
    fireEvent.click(button)

    expect(await screen.findByText("library failed")).toBeTruthy()
    await waitFor(() => {
      expect((button as HTMLButtonElement).disabled).toBe(false)
    })
  })
})
