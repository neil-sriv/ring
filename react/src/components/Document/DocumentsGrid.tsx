import { Button } from "@/components/ui/button"
import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { FileText, Loader2 } from "lucide-react"
import { useRef } from "react"
import type {
  CreateDocumentEndpointNotebookDocumentsPostError,
  DocumentResponse,
} from "../../client"
import {
  createDocumentEndpointNotebookDocumentsPostMutation,
  listDocumentsNotebookDocumentsGetOptions,
  listDocumentsNotebookDocumentsGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"
import { DocumentCard } from "./DocumentCard"

export function DocumentsGrid(props: {
  groupApiId: string
}): JSX.Element {
  const { data: documents } = useSuspenseQuery({
    ...listDocumentsNotebookDocumentsGetOptions({
      query: {
        group_api_id: props.groupApiId,
      },
    }),
  })

  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  // disabled={isPending} alone still lets a second click through before React
  // re-renders; this ref closes that same-tick double-create window.
  const createInFlightRef = useRef(false)

  const createDocumentMutation = useMutation({
    ...createDocumentEndpointNotebookDocumentsPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listDocumentsNotebookDocumentsGetQueryKey({
          query: { group_api_id: props.groupApiId },
        }),
      })
    },
    onError: (
      err: AxiosError<CreateDocumentEndpointNotebookDocumentsPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
  })

  const isCreating = createDocumentMutation.isPending

  const createDocument = async (name: string) => {
    if (createInFlightRef.current || isCreating) {
      return
    }
    createInFlightRef.current = true
    try {
      await createDocumentMutation.mutateAsync({
        body: {
          group_api_id: props.groupApiId,
          name,
          content: "",
        },
      })
    } catch {
      // onError already toasts
    } finally {
      createInFlightRef.current = false
    }
  }

  return (
    <div className="flex w-full flex-col gap-6">
      <div className="flex w-full items-center justify-between gap-4">
        <h3 className="text-base font-semibold">Documents</h3>
        <Button
          size="sm"
          disabled={isCreating}
          onClick={() => {
            void createDocument("Untitled Document")
          }}
        >
          {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          New Document
        </Button>
      </div>

      {documents.length === 0 ? (
        <div className="flex w-full flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
          <FileText
            className="h-8 w-8 text-muted-foreground/60"
            strokeWidth={1.5}
          />
          <h3 className="mt-4 font-display text-lg font-medium">
            No documents yet
          </h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Create your first collaborative document to get started
          </p>
          <Button
            className="mt-6"
            disabled={isCreating}
            onClick={() => {
              void createDocument("My First Document")
            }}
          >
            {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Document
          </Button>
        </div>
      ) : (
        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {documents.map((document: DocumentResponse) => (
            <DocumentCard key={document.api_identifier} document={document} />
          ))}
        </div>
      )}
    </div>
  )
}
