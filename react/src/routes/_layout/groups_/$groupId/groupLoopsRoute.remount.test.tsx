import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { GroupLinked, UserLinked } from "../../../../client"
import {
  getUnreadCountNotificationsInboxUnreadCountGetQueryKey,
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listLettersLettersLettersGetQueryKey,
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readSpotifyStatusSpotifyStatusGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../../../client/@tanstack/react-query.gen"
import { client } from "../../../../client/client.gen"
import { routeTree } from "../../../../routeTree.gen"

const GROUP_A = "grp_a"
const GROUP_B = "grp_b"

const ada = {
  email: "ada@example.com",
  name: "Ada",
  api_identifier: "usr_ada",
  admin: false,
}

const currentUser = {
  ...ada,
  groups: [],
} satisfies UserLinked

function ok(data: unknown) {
  return {
    data,
    status: 200,
    statusText: "OK",
    headers: {},
    config: {},
  }
}

function group(id: string, name: string): GroupLinked {
  return {
    name,
    api_identifier: id,
    created_at: "2026-11-01T00:00:00.000Z",
    cycle_length: 7,
    members: [ada],
    admin: ada,
    default_questions: [],
  }
}

const groupA = group(GROUP_A, "Group A")
const groupB = group(GROUP_B, "Group B")

function installClient() {
  vi.spyOn(client, "get").mockImplementation((async (options) => {
    const request = options as {
      url?: string
      path?: { group_api_id?: string }
    }
    const url = request.url ?? ""
    if (url.includes("/parties/me")) {
      return ok(currentUser)
    }
    if (url.includes("/letters/letters:dashboard")) {
      return ok({ upcoming: [], in_progress: [], recently_completed: [] })
    }
    if (url.includes("/letters/letters")) {
      return ok([])
    }
    if (url.includes("/key-value")) {
      return ok({ key_values: {} })
    }
    if (url.includes("/parties/group/")) {
      const found = [groupA, groupB].find(
        (item) => item.api_identifier === request.path?.group_api_id,
      )
      if (!found) {
        throw new Error(`missing group ${request.path?.group_api_id}`)
      }
      return ok(found)
    }
    if (url.includes("/unread-count")) {
      return ok({ unread_count: 0 })
    }
    if (url.includes("/notifications/inbox")) {
      return ok([])
    }
    if (url.includes("/spotify/status")) {
      return ok({ configured: false, linked: false })
    }
    throw new Error(`unexpected GET ${url}`)
  }) as typeof client.get)
}

function seed(queryClient: QueryClient) {
  queryClient.setQueryData(readUserMePartiesMeGetQueryKey(), currentUser)
  queryClient.setQueryData(
    listDashboardLettersLettersLettersDashboardGetQueryKey(),
    { upcoming: [], in_progress: [], recently_completed: [] },
  )
  queryClient.setQueryData(
    getUnreadCountNotificationsInboxUnreadCountGetQueryKey(),
    { unread_count: 0 },
  )
  queryClient.setQueryData(readSpotifyStatusSpotifyStatusGetQueryKey(), {
    configured: false,
    linked: false,
  })
  for (const item of [groupA, groupB]) {
    queryClient.setQueryData(
      readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: item.api_identifier },
      }),
      item,
    )
    queryClient.setQueryData(
      listLettersLettersLettersGetQueryKey({
        query: {
          group_api_id: item.api_identifier,
          skip: undefined,
          limit: undefined,
        },
      }),
      [],
    )
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("group loops page remounts when groupId changes", () => {
  it("closes an open add-loop dialog when navigating to another group", async () => {
    installClient()
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: Number.POSITIVE_INFINITY,
          refetchOnMount: false,
          refetchOnWindowFocus: false,
        },
        mutations: { retry: false },
      },
    })
    seed(queryClient)
    const router = createRouter({
      routeTree,
      history: createMemoryHistory({
        initialEntries: [`/groups/${GROUP_A}/loops`],
      }),
      context: {
        queryClient,
        auth: { user: currentUser, isAuthenticated: true },
      },
    })
    await router.load()
    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    )

    expect(await screen.findByRole("heading", { name: "Group A" })).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: "Start Next Loop" }))
    expect(await screen.findByRole("dialog")).toBeTruthy()
    fireEvent.change(screen.getByLabelText(/Send at/), {
      target: { value: "2030-01-02T09:30" },
    })

    await act(async () => {
      await router.navigate({
        to: "/groups/$groupId/loops",
        params: { groupId: GROUP_B },
      })
    })

    expect(await screen.findByRole("heading", { name: "Group B" })).toBeTruthy()
    expect(screen.queryByRole("dialog")).toBeNull()
    expect(screen.queryByLabelText(/Send at/)).toBeNull()
  })
})
