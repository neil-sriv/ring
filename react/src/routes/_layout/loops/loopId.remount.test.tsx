import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  RouterProvider,
  createMemoryHistory,
  createRouter,
} from "@tanstack/react-router"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { GroupLinked, PublicLetter, UserLinked } from "../../../client"
import {
  getUnreadCountNotificationsInboxUnreadCountGetQueryKey,
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readSpotifyStatusSpotifyStatusGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../../client/@tanstack/react-query.gen"
import { client } from "../../../client/client.gen"
import { routeTree } from "../../../routeTree.gen"

const LOOP_A = "lttr_a"
const LOOP_B = "lttr_b"
const GROUP_A = "grp_a"
const GROUP_B = "grp_b"
const LATE_TEXT = "What did A eat?"
const GROUP_A_ERROR = "group A failed to load"

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

type ApiRequest = {
  url?: string
  path?: { group_api_id?: string; letter_api_id?: string }
  body?: { question_text?: string }
}

const posts: ApiRequest[] = []

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

function letter(id: string, groupId: string, title: string): PublicLetter {
  const owner = group(groupId, title)
  return {
    api_identifier: id,
    status: "IN_PROGRESS",
    send_at: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: "2026-11-01T00:00:00.000Z",
    title,
    letter_type: "CYCLIC",
    group: {
      api_identifier: owner.api_identifier,
      name: owner.name,
      created_at: owner.created_at,
      cycle_length: owner.cycle_length,
    },
    questions: [],
    responders: [],
    participants: [ada],
  }
}

const letterA = letter(LOOP_A, GROUP_A, "Loop A")
const letterB = letter(LOOP_B, GROUP_B, "Loop B")
const groupA = group(GROUP_A, "Group A")
const groupB = group(GROUP_B, "Group B")

function installClient(failingGroupIds: ReadonlySet<string>) {
  posts.length = 0
  vi.spyOn(client, "get").mockImplementation((async (options) => {
    const request = options as ApiRequest
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
    if (url.includes("/letters/letter/")) {
      const found = [letterA, letterB].find(
        (loop) => loop.api_identifier === request.path?.letter_api_id,
      )
      if (!found) {
        throw new Error(`missing letter ${request.path?.letter_api_id}`)
      }
      return ok(found)
    }
    if (url.includes("/parties/group/")) {
      const groupId = request.path?.group_api_id
      if (groupId && failingGroupIds.has(groupId)) {
        throw new Error(GROUP_A_ERROR)
      }
      const found = [groupA, groupB].find(
        (item) => item.api_identifier === groupId,
      )
      if (!found) {
        throw new Error(`missing group ${groupId}`)
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
  vi.spyOn(client, "post").mockImplementation((async (options) => {
    posts.push(options as ApiRequest)
    return ok({})
  }) as typeof client.post)
}

function seed(queryClient: QueryClient, failingGroupIds: ReadonlySet<string>) {
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
  for (const loop of [letterA, letterB]) {
    queryClient.setQueryData(
      readLetterLettersLetterLetterApiIdGetQueryKey({
        path: { letter_api_id: loop.api_identifier },
      }),
      loop,
    )
  }
  for (const item of [groupA, groupB]) {
    if (failingGroupIds.has(item.api_identifier)) {
      continue
    }
    queryClient.setQueryData(
      readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: item.api_identifier },
      }),
      item,
    )
  }
}

async function renderLoop(
  loopId: string,
  failingGroupIds: ReadonlySet<string>,
) {
  installClient(failingGroupIds)
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
  seed(queryClient, failingGroupIds)
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({
      initialEntries: [`/loops/${loopId}`],
    }),
    context: {
      queryClient,
      auth: { user: currentUser, isAuthenticated: true },
    },
  })
  await router.load()
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { router, ...view }
}

afterEach(() => {
  cleanup()
  posts.length = 0
  vi.restoreAllMocks()
})

describe("loop page remounts when loopId changes", () => {
  it("drops a typed late question instead of saving it onto the next loop", async () => {
    const { router } = await renderLoop(LOOP_A, new Set())
    expect(await screen.findByRole("heading", { name: "Loop A" })).toBeTruthy()

    fireEvent.click(screen.getByRole("button", { name: "Add a late question" }))
    fireEvent.change(screen.getByLabelText("What should everyone answer?"), {
      target: { value: LATE_TEXT },
    })
    expect(screen.getByDisplayValue(LATE_TEXT)).toBeTruthy()

    await act(async () => {
      await router.navigate({
        to: "/loops/$loopId",
        params: { loopId: LOOP_B },
      })
    })

    expect(await screen.findByRole("heading", { name: "Loop B" })).toBeTruthy()
    expect(
      screen.getByRole("button", { name: "Add a late question" }),
    ).toBeTruthy()
    expect(
      screen.queryByRole("button", { name: "Hide late question" }),
    ).toBeNull()
    expect(screen.queryByLabelText("What should everyone answer?")).toBeNull()
    expect(screen.queryByDisplayValue(LATE_TEXT)).toBeNull()
    expect(
      posts.filter(
        (request) =>
          request.url?.includes("add_question") &&
          request.path?.letter_api_id === LOOP_B &&
          request.body?.question_text === LATE_TEXT,
      ),
    ).toEqual([])
  })

  it("shows the next loop after the previous loop's query fails", async () => {
    const { router } = await renderLoop(LOOP_A, new Set([GROUP_A]))
    expect(await screen.findByText(GROUP_A_ERROR)).toBeTruthy()
    expect(screen.queryByRole("heading", { name: "Loop A" })).toBeNull()

    await act(async () => {
      await router.navigate({
        to: "/loops/$loopId",
        params: { loopId: LOOP_B },
      })
    })

    expect(await screen.findByRole("heading", { name: "Loop B" })).toBeTruthy()
    expect(screen.queryByText(GROUP_A_ERROR)).toBeNull()
  })
})
