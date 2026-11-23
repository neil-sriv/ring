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

import type { SpotifyPlaylistResponse, SpotifyStatus } from "../../client"
import { readSpotifyStatusSpotifyStatusGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import { GroupSpotifyPlaylist } from "./GroupSpotifyPlaylist"

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
}))

const statusLinked = {
  configured: true,
  linked: true,
} satisfies SpotifyStatus

const playlist = {
  playlist_id: "pl_seed",
  playlist_url: "https://open.spotify.com/playlist/pl_seed",
  name: "Cloud Seed Group",
  track_count: 2,
} satisfies SpotifyPlaylistResponse

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

function PlaylistHarness() {
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
      <GroupSpotifyPlaylist groupId="grp_seed" groupName="Cloud Seed Group" />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("GroupSpotifyPlaylist", () => {
  it("ensures with a finite request timeout", async () => {
    vi.spyOn(client, "get").mockResolvedValue({
      data: null,
      status: 404,
      statusText: "Not Found",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.get>>)

    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: playlist,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<PlaylistHarness />)

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Add this group's songs to your Spotify",
      }),
    )

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as { timeout?: number }
    expect(call.timeout).toBe(60_000)

    expect(
      await screen.findByText("Playlist updated in your Spotify account."),
    ).toBeTruthy()
  })

  it("toasts a timeout message and unlocks the button", async () => {
    vi.spyOn(client, "get").mockResolvedValue({
      data: null,
      status: 404,
      statusText: "Not Found",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.get>>)
    vi.spyOn(client, "post").mockRejectedValue(timeoutError())

    render(<PlaylistHarness />)

    const button = await screen.findByRole("button", {
      name: "Add this group's songs to your Spotify",
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
    vi.spyOn(client, "get").mockResolvedValue({
      data: null,
      status: 404,
      statusText: "Not Found",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.get>>)
    vi.spyOn(client, "post").mockRejectedValue(serverError("spotify exploded"))

    render(<PlaylistHarness />)

    const button = await screen.findByRole("button", {
      name: "Add this group's songs to your Spotify",
    })
    fireEvent.click(button)

    expect(await screen.findByText("spotify exploded")).toBeTruthy()
    await waitFor(() => {
      expect((button as HTMLButtonElement).disabled).toBe(false)
    })
  })
})
