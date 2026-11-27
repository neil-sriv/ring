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

import type { DocumentResponse } from "../../client"
import { listDocumentsNotebookDocumentsGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { client } from "../../client/client.gen"
import { DocumentsGrid } from "./DocumentsGrid"

const navigate = vi.fn()

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => navigate,
}))

const createdDocument = {
  name: "Untitled Document",
  api_identifier: "doc_created",
  content: "",
  latest_snapshot_version: 0,
  created_at: "2026-11-27T00:00:00.000Z",
  updated_at: "2026-11-27T00:00:00.000Z",
} satisfies DocumentResponse

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

function DocumentsGridHarness() {
  const [queryClient] = useState(() => {
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Number.POSITIVE_INFINITY },
        mutations: { retry: false },
      },
    })
    qc.setQueryData(
      listDocumentsNotebookDocumentsGetQueryKey({
        query: { group_api_id: "grp_seed" },
      }),
      [],
    )
    return qc
  })
  return (
    <QueryClientProvider client={queryClient}>
      <DocumentsGrid groupApiId="grp_seed" />
      <Toaster />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  navigate.mockReset()
  vi.restoreAllMocks()
})

describe("DocumentsGrid create", () => {
  it("submits with a finite request timeout", async () => {
    const post = vi.spyOn(client, "post").mockResolvedValue({
      data: createdDocument,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof client.post>>)

    render(<DocumentsGridHarness />)
    fireEvent.click(screen.getByRole("button", { name: "New Document" }))

    await waitFor(() => {
      expect(post).toHaveBeenCalled()
    })

    const call = post.mock.calls[0]?.[0] as {
      body?: { group_api_id?: string; name?: string; content?: string }
      timeout?: number
    }
    expect(call.timeout).toBe(20_000)
    expect(call.body).toEqual({
      group_api_id: "grp_seed",
      name: "Untitled Document",
      content: "",
    })

    expect(
      await screen.findByText("Document created successfully."),
    ).toBeTruthy()
    expect(navigate).toHaveBeenCalledWith({
      to: "/documents/$documentId",
      params: { documentId: "doc_created" },
    })
  })

  it("recovers from a 500 and unlocks New Document", async () => {
    vi.spyOn(client, "post").mockRejectedValue(serverError("create exploded"))

    render(<DocumentsGridHarness />)
    fireEvent.click(screen.getByRole("button", { name: "New Document" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(screen.getByText("create exploded")).toBeTruthy()

    await waitFor(() => {
      expect(
        (
          screen.getByRole("button", {
            name: "New Document",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false)
    })
    expect(navigate).not.toHaveBeenCalled()
  })

  it("recovers from a network error with no response body", async () => {
    vi.spyOn(client, "post").mockRejectedValue(networkError())

    render(<DocumentsGridHarness />)
    fireEvent.click(screen.getByRole("button", { name: "Create Document" }))

    expect(await screen.findByText("Something went wrong.")).toBeTruthy()
    expect(
      screen.getByText("Something went wrong. Please try again."),
    ).toBeTruthy()

    await waitFor(() => {
      expect(
        (
          screen.getByRole("button", {
            name: "Create Document",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false)
    })
  })
})
