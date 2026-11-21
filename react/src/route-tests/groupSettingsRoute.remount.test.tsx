import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { GroupLinked, UserLinked } from "../client"
import {
  getUnreadCountNotificationsInboxUnreadCountGetQueryKey,
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readSpotifyStatusSpotifyStatusGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../client/@tanstack/react-query.gen"
import { client } from "../client/client.gen"
import { routeTree } from "../routeTree.gen"

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

function group(
  id: string,
  name: string,
  cycleLength: number,
  question: string,
): GroupLinked {
  return {
    name,
    api_identifier: id,
    created_at: "2026-11-01T00:00:00.000Z",
    cycle_length: cycleLength,
    members: [ada],
    admin: ada,
    default_questions: [
      {
        question_text: question,
        api_identifier: `q_${id}`,
        created_at: "2026-11-01T00:00:00.000Z",
      },
    ],
  }
}

const groupA = group(GROUP_A, "Group A", 7, "Question from A")
const groupB = group(GROUP_B, "Group B", 30, "Question from B")

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
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe("group settings page remounts when groupId changes", () => {
  it("reseeds the loop settings form from the next group", async () => {
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
        initialEntries: [`/groups/${GROUP_A}/settings`],
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

    expect((await screen.findAllByText("Group A")).length).toBeGreaterThan(0)
    const loopTab = screen.getByRole("tab", { name: "Loop Settings" })
    fireEvent.mouseDown(loopTab)
    fireEvent.click(loopTab)
    expect(screen.getByText("7 days")).toBeTruthy()
    expect(screen.getByText("Question from A")).toBeTruthy()

    fireEvent.click(screen.getByRole("button", { name: "Edit" }))
    fireEvent.change(screen.getByLabelText("Loop Cycle (days)"), {
      target: { value: "21" },
    })
    expect(screen.getByDisplayValue("21")).toBeTruthy()

    await act(async () => {
      await router.navigate({
        to: "/groups/$groupId/settings",
        params: { groupId: GROUP_B },
      })
    })

    expect((await screen.findAllByText("Group B")).length).toBeGreaterThan(0)
    expect(screen.queryByText("Group A")).toBeNull()
    const nextLoopTab = screen.getByRole("tab", { name: "Loop Settings" })
    fireEvent.mouseDown(nextLoopTab)
    fireEvent.click(nextLoopTab)
    expect(screen.getByText("30 days")).toBeTruthy()
    expect(screen.getByText("Question from B")).toBeTruthy()
    expect(screen.queryByText("Question from A")).toBeNull()
    expect(screen.queryByDisplayValue("21")).toBeNull()
    expect(screen.getByRole("button", { name: "Edit" })).toBeTruthy()
    expect(screen.queryByRole("button", { name: "Save" })).toBeNull()
  })
})
