import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { Suspense, useState } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey } from "../client/@tanstack/react-query.gen"
import { client } from "../client/client.gen"
import { GroupStoreTab } from "../routes/_layout/groups_/$groupId/loops"

const GROUP_A = "grp_a"
const GROUP_B = "grp_b"

vi.mock("react-json-view", () => ({
  default: function MockReactJson({
    src,
    onEdit,
  }: {
    src: Record<string, unknown>
    onEdit?: (edit: { updated_src: Record<string, unknown> }) => void
  }) {
    return (
      <div>
        <span>{JSON.stringify(src)}</span>
        <button
          type="button"
          onClick={() => {
            onEdit?.({ updated_src: { ...src, edited: true } })
          }}
        >
          onEdit
        </button>
      </div>
    )
  },
}))

function seedKeyValues(queryClient: QueryClient) {
  queryClient.setQueryData(
    readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey({
      path: { group_api_id: GROUP_A },
    }),
    { key_values: { a: 1 } },
  )
  queryClient.setQueryData(
    readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey({
      path: { group_api_id: GROUP_B },
    }),
    { key_values: { b: 2 } },
  )
}

function StoreHarness({
  initialGroupId,
}: {
  initialGroupId: string
}) {
  const [groupId, setGroupId] = useState(initialGroupId)
  const [queryClient] = useState(() => {
    const next = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
    seedKeyValues(next)
    return next
  })

  return (
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div>loading</div>}>
        <GroupStoreTab groupId={groupId} />
      </Suspense>
      <button type="button" onClick={() => setGroupId(GROUP_B)}>
        switch-group
      </button>
    </QueryClientProvider>
  )
}

function putTargets() {
  return vi.mocked(client.put).mock.calls.map((call) => {
    const options = call[0] as {
      path?: { group_api_id?: string }
      body?: { key_values?: Record<string, unknown> }
    }
    return {
      groupApiId: options.path?.group_api_id,
      keyValues: options.body?.key_values,
    }
  })
}

async function settleEditor() {
  await act(async () => {
    await vi.dynamicImportSettled()
  })
}

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.restoreAllMocks()
})

describe("GroupStoreTab", () => {
  it("shows only the next group's store when groupId changes", async () => {
    render(<StoreHarness initialGroupId={GROUP_A} />)
    await settleEditor()

    expect(screen.getByText('{"a":1}')).toBeTruthy()

    fireEvent.click(screen.getByRole("button", { name: "switch-group" }))
    await settleEditor()

    expect(screen.getByText('{"b":2}')).toBeTruthy()
    expect(screen.queryByText('{"a":1}')).toBeNull()
  })

  it("flushes a pending edit to the previous group when switching within 1s", async () => {
    vi.useFakeTimers()
    vi.spyOn(client, "put").mockResolvedValue({
      data: { key_values: {} },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.put>>)

    render(<StoreHarness initialGroupId={GROUP_A} />)
    await settleEditor()

    fireEvent.click(screen.getByRole("button", { name: "onEdit" }))
    expect(screen.getByText('{"a":1,"edited":true}')).toBeTruthy()

    await act(async () => {
      vi.advanceTimersByTime(999)
    })
    expect(client.put).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole("button", { name: "switch-group" }))
    await settleEditor()

    expect(putTargets()).toEqual([
      { groupApiId: GROUP_A, keyValues: { a: 1, edited: true } },
    ])
    expect(screen.getByText('{"b":2}')).toBeTruthy()
    expect(screen.queryByText('{"a":1,"edited":true}')).toBeNull()

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(putTargets()).toEqual([
      { groupApiId: GROUP_A, keyValues: { a: 1, edited: true } },
    ])
  })

  it("sends an edit on the current group to that group's path", async () => {
    vi.useFakeTimers()
    vi.spyOn(client, "put").mockResolvedValue({
      data: { key_values: {} },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.put>>)

    render(<StoreHarness initialGroupId={GROUP_B} />)
    await settleEditor()

    fireEvent.click(screen.getByRole("button", { name: "onEdit" }))
    expect(screen.getByText('{"b":2,"edited":true}')).toBeTruthy()
    expect(client.put).not.toHaveBeenCalled()

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    expect(putTargets()).toEqual([
      { groupApiId: GROUP_B, keyValues: { b: 2, edited: true } },
    ])
  })
})
