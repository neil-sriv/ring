import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, render, waitFor } from "@testing-library/react"
import { act } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import type { Doc } from "yjs"

import type { UserLinked } from "@/client"
import { readUserMePartiesMeGetQueryKey } from "@/client/@tanstack/react-query.gen"
import { apiUrl } from "@/lib/apiUrl"

import { CollabEditor } from "./Editor"

type RecordedProvider = {
  serverUrl: string
  docName: string
  doc: Doc
  synced: boolean
  destroyed: boolean
  text: string
  fragmentAtDestroy: string
  listenerCount: (event: string) => number
}

const harness = vi.hoisted(() => {
  return {
    providers: [] as RecordedProvider[],
    boundDocs: [] as Doc[],
    editors: [] as Array<{
      commands: { insertContent: (text: string) => boolean }
    }>,
  }
})

vi.mock("y-websocket", () => {
  class FakeAwareness {
    states = new Map<number, Record<string, unknown>>()
    clientID = 1
    private listeners = new Map<string, Set<() => void>>()

    on(event: string, callback: () => void) {
      const callbacks = this.listeners.get(event) ?? new Set<() => void>()
      callbacks.add(callback)
      this.listeners.set(event, callbacks)
    }

    off(event: string, callback: () => void) {
      this.listeners.get(event)?.delete(callback)
    }

    getStates() {
      return this.states
    }

    getLocalState() {
      return this.states.get(this.clientID) ?? null
    }

    setLocalStateField(field: string, value: unknown) {
      const current = this.states.get(this.clientID) ?? {}
      this.states.set(this.clientID, { ...current, [field]: value })
      for (const callback of this.listeners.get("update") ?? []) {
        callback()
      }
      for (const callback of this.listeners.get("change") ?? []) {
        callback()
      }
    }
  }

  class WebsocketProvider implements RecordedProvider {
    serverUrl: string
    docName: string
    doc: Doc
    synced = true
    destroyed = false
    text = ""
    fragmentAtDestroy = ""
    awareness: FakeAwareness
    private listeners = new Map<string, Set<() => void>>()
    private onDocUpdate: () => void

    constructor(serverUrl: string, docName: string, doc: Doc) {
      this.serverUrl = serverUrl
      this.docName = docName
      this.doc = doc
      this.awareness = new FakeAwareness()
      this.onDocUpdate = () => {
        this.text = doc.getXmlFragment("default").toString()
      }
      doc.on("update", this.onDocUpdate)
      harness.providers.push(this)
    }

    listenerCount(event: string) {
      return this.listeners.get(event)?.size ?? 0
    }

    on(event: string, callback: () => void) {
      const callbacks = this.listeners.get(event) ?? new Set<() => void>()
      callbacks.add(callback)
      this.listeners.set(event, callbacks)
    }

    off(event: string, callback: () => void) {
      this.listeners.get(event)?.delete(callback)
    }

    destroy() {
      if (this.destroyed) {
        return
      }
      this.fragmentAtDestroy = this.doc.getXmlFragment("default").toString()
      this.destroyed = true
      this.listeners.clear()
      this.doc.off("update", this.onDocUpdate)
      this.doc.destroy()
    }
  }

  return { WebsocketProvider }
})

vi.mock("@tiptap/react", async () => {
  const actual =
    await vi.importActual<typeof import("@tiptap/react")>("@tiptap/react")
  return {
    ...actual,
    useEditor: (
      options: Parameters<typeof actual.useEditor>[0],
      deps?: Parameters<typeof actual.useEditor>[1],
    ) => {
      for (const extension of options.extensions ?? []) {
        const configured = extension as {
          name: string
          options?: { document?: Doc | null }
        }
        if (
          configured.name !== "collaboration" ||
          !configured.options?.document
        ) {
          continue
        }
        harness.boundDocs.push(configured.options.document)
      }
      const editor = actual.useEditor(options, deps)
      if (editor) {
        harness.editors.push(editor)
      }
      return editor
    },
  }
})

const me: UserLinked = {
  email: "ada@example.com",
  name: "Ada",
  api_identifier: "usr_ada",
  admin: false,
  groups: [],
}

const LEGACY_B = "<p>Hello from B</p>"

function createQueryClient() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Number.POSITIVE_INFINITY,
      },
    },
  })
  queryClient.setQueryData(readUserMePartiesMeGetQueryKey({}), me)
  return queryClient
}

function EditorHarness({
  client,
  docId,
  legacyContent,
}: {
  client: QueryClient
  docId: string
  legacyContent?: string
}) {
  return (
    <QueryClientProvider client={client}>
      <CollabEditor docId={docId} legacyContent={legacyContent} />
    </QueryClientProvider>
  )
}

function providerFor(docName: string): RecordedProvider | undefined {
  for (let index = harness.providers.length - 1; index >= 0; index -= 1) {
    const provider = harness.providers[index]
    if (provider?.docName === docName) {
      return provider
    }
  }
  return undefined
}

describe("CollabEditor document switches", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(
          JSON.stringify({
            api_identifier: "doc",
            name: "Doc",
            content: "",
            latest_snapshot_version: 1,
            created_at: "2026-11-21T00:00:00.000Z",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        )
      }),
    )
  })

  afterEach(() => {
    cleanup()
    harness.providers.length = 0
    harness.boundDocs.length = 0
    harness.editors.length = 0
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it("binds each editor to that document's Y.Doc and seeds legacy HTML on the new provider", async () => {
    const client = createQueryClient()
    const view = render(<EditorHarness client={client} docId="doc_a" />)

    await waitFor(() => {
      expect(providerFor("doc_a")).toBeDefined()
      expect(harness.boundDocs).toContain(providerFor("doc_a")?.doc)
    })

    const providerA = providerFor("doc_a")
    if (!providerA) {
      throw new Error("missing provider for doc_a")
    }
    const ydocA = providerA.doc
    const boundBeforeSwitch = harness.boundDocs.length

    view.rerender(
      <EditorHarness client={client} docId="doc_b" legacyContent={LEGACY_B} />,
    )

    await waitFor(() => {
      const providerB = providerFor("doc_b")
      expect(providerB?.text).toContain("Hello from B")
    })

    const providerB = providerFor("doc_b")
    if (!providerB) {
      throw new Error("missing provider for doc_b")
    }
    const bindingsAfterSwitch = harness.boundDocs.slice(boundBeforeSwitch)

    expect(providerA.docName).toBe("doc_a")
    expect(providerB.docName).toBe("doc_b")
    expect(providerB.doc).not.toBe(ydocA)
    expect(bindingsAfterSwitch).not.toContain(ydocA)
    expect(bindingsAfterSwitch).toContain(providerB.doc)
    expect(providerB.listenerCount("sync")).toBeGreaterThan(0)
    expect(providerA.fragmentAtDestroy).not.toContain("Hello from B")
    expect(providerA.destroyed).toBe(true)
  })

  it("flushes the pending HTML save once, to the document that was edited, on unmount", async () => {
    const puts: Array<{ url: string; method: string; body: string }> = []
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        puts.push({
          url: String(input),
          method: init?.method ?? "GET",
          body: typeof init?.body === "string" ? init.body : "",
        })
        return new Response(
          JSON.stringify({
            api_identifier: "doc_a",
            name: "A",
            content: "<p>Kept</p>",
            latest_snapshot_version: 1,
            created_at: "2026-11-21T00:00:00.000Z",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        )
      }),
    )

    const client = createQueryClient()
    const view = render(<EditorHarness client={client} docId="doc_a" />)

    await waitFor(() => {
      expect(document.querySelector(".prosemirror-editor")).not.toBeNull()
      expect(harness.editors.length).toBeGreaterThan(0)
    })

    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] })
    const editor = harness.editors[harness.editors.length - 1]
    if (!editor) {
      throw new Error("editor was not created")
    }

    act(() => {
      editor.commands.insertContent("Kept")
    })
    expect(puts).toEqual([])

    view.unmount()

    expect(puts).toHaveLength(1)
    expect(puts[0]?.method).toBe("PUT")
    expect(puts[0]?.url).toBe(apiUrl("/api/v1/notebook/documents/doc_a"))
    expect(puts[0]?.body).toContain("Kept")

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(puts).toHaveLength(1)
  })
})
