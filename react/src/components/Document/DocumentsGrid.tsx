import { Button } from "@/components/ui/button"
import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
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
    <div className="p-4">
      <div className="flex flex-col items-start gap-6">
        <div className="flex justify-between items-center w-full">
          <h2 className="text-2xl font-bold text-foreground">Documents</h2>
          <div className="flex gap-3">
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
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-12 w-full backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 rounded-xl">
            <div className="flex flex-col items-center gap-4">
              <p className="text-lg text-foreground">No documents yet</p>
              <p className="text-sm text-muted-foreground">
                Create your first collaborative document to get started
              </p>
              <Button
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
                Create Document
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full">
            {documents.map((document: DocumentResponse) => (
              <DocumentCard key={document.api_identifier} document={document} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
