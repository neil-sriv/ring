import { Button } from "@/components/ui/button"
import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { FileText, Loader2 } from "lucide-react"
import type { DocumentResponse } from "../../client"
import {
  createDocumentEndpointNotebookDocumentsPostMutation,
  listDocumentsNotebookDocumentsGetOptions,
  listDocumentsNotebookDocumentsGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
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

  const createDocumentMutation = useMutation({
    ...createDocumentEndpointNotebookDocumentsPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listDocumentsNotebookDocumentsGetQueryKey({
          query: { group_api_id: props.groupApiId },
        }),
      })
    },
  })

  return (
    <div className="flex w-full flex-col gap-6">
      <div className="flex w-full items-center justify-between gap-4">
        <h3 className="text-base font-semibold">Documents</h3>
        <Button
          size="sm"
          disabled={createDocumentMutation.isPending}
          onClick={() => {
            createDocumentMutation.mutate({
              body: {
                group_api_id: props.groupApiId,
                name: "Untitled Document",
                content: "",
              },
            })
          }}
        >
          {createDocumentMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
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
            disabled={createDocumentMutation.isPending}
            onClick={() => {
              createDocumentMutation.mutate({
                body: {
                  group_api_id: props.groupApiId,
                  name: "My First Document",
                  content: "",
                },
              })
            }}
          >
            {createDocumentMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
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
