import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { Suspense, lazy, useRef, useState } from "react"
import type { DocumentResponse } from "../../../client"
import {
  getDocumentEndpointNotebookDocumentsDocumentApiIdGetOptions,
  getDocumentEndpointNotebookDocumentsDocumentApiIdGetQueryKey,
  updateDocumentEndpointNotebookDocumentsDocumentApiIdPutMutation,
} from "../../../client/@tanstack/react-query.gen"
import { EditableTitle } from "../../../components/Document/EditableTitle"

type DocumentLoaderProps = {
  document: DocumentResponse
}

const CollabEditor = lazy(() =>
  import("../../../components/Document/Editor").then((module) => ({
    default: module.CollabEditor,
  })),
)

export const Route = createFileRoute("/_layout/documents/$documentId")({
  loader: async ({ params, context }): Promise<DocumentLoaderProps> => {
    const document = await context.queryClient.ensureQueryData({
      ...getDocumentEndpointNotebookDocumentsDocumentApiIdGetOptions({
        path: {
          document_api_id: params.documentId,
        },
      }),
    })

    return {
      document,
    }
  },
  component: DocumentContent,
})

function DocumentContentLoader() {
  const documentId = Route.useParams().documentId
  const [isSaving, setIsSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const savingStartTimeRef = useRef<number | null>(null)
  const queryClient = useQueryClient()

  // Use query data instead of loader data to get real-time updates
  const { data: document, isLoading: isDocumentLoading } = useQuery({
    ...getDocumentEndpointNotebookDocumentsDocumentApiIdGetOptions({
      path: { document_api_id: documentId },
    }),
  })

  const updateDocumentMutation = useMutation({
    ...updateDocumentEndpointNotebookDocumentsDocumentApiIdPutMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getDocumentEndpointNotebookDocumentsDocumentApiIdGetQueryKey({
          path: { document_api_id: documentId },
        }),
      })
    },
  })

  const handleSavingChange = (saving: boolean) => {
    if (saving) {
      savingStartTimeRef.current = Date.now()
      setIsSaving(true)
    } else {
      const elapsed = Date.now() - (savingStartTimeRef.current || 0)
      const remainingTime = Math.max(0, 500 - elapsed)

      setTimeout(() => {
        setIsSaving(false)
      }, remainingTime)
    }
  }

  const handleTitleChange = async (newTitle: string) => {
    await updateDocumentMutation.mutateAsync({
      path: {
        document_api_id: documentId,
      },
      body: {
        name: newTitle,
      },
    })
  }

  if (isDocumentLoading) {
    return (
      <div className="w-full mt-8">
        <div className="text-center py-8">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
        </div>
      </div>
    )
  }

  if (!document) {
    return (
      <div className="w-full mt-8">
        <div className="text-center py-8">
          <p>Document not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full mt-8 px-4">
      <div className="backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 p-6 rounded-xl shadow-md mb-6">
        <div className="flex justify-between items-center">
          <EditableTitle
            title={document.name}
            onTitleChange={handleTitleChange}
            isLoading={updateDocumentMutation.isPending}
            size="lg"
            textAlign="left"
          />
          <div className="flex items-center gap-2 bg-white/20 px-3 py-1 rounded-md border border-white/30 dark:bg-white/10 dark:border-white/20">
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Syncing...
                </span>
              </>
            ) : isEditing ? (
              <span className="text-sm text-orange-600 dark:text-orange-400">
                Editing...
              </span>
            ) : (
              <span className="text-sm text-green-600 dark:text-green-400">
                Saved
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 p-6 rounded-xl shadow-md">
        <Suspense
          fallback={<Loader2 className="h-8 w-8 animate-spin mx-auto" />}
        >
          <CollabEditor
            docId={documentId}
            onSavingChange={handleSavingChange}
            onEditingChange={setIsEditing}
          />
        </Suspense>
      </div>
    </div>
  )
}

function DocumentContent() {
  return <DocumentContentLoader />
}
