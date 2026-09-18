import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { Suspense, lazy, useRef, useState } from "react"
import { toast } from "sonner"
import type { DocumentResponse } from "../../../client"
import {
  getDocumentEndpointNotebookDocumentsDocumentApiIdGetOptions,
  getDocumentEndpointNotebookDocumentsDocumentApiIdGetQueryKey,
  updateDocumentEndpointNotebookDocumentsDocumentApiIdPutMutation,
} from "../../../client/@tanstack/react-query.gen"
import { EditableTitle } from "../../../components/Document/EditableTitle"
import type { NotebookWsStatus } from "../../../components/Document/Editor"

const SYNC_ERROR_TOAST_COOLDOWN_MS = 10_000

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
  const [hasSyncError, setHasSyncError] = useState(false)
  const [wsStatus, setWsStatus] = useState<NotebookWsStatus>("connecting")
  const savingStartTimeRef = useRef<number | null>(null)
  const lastSyncErrorToastAtRef = useRef(0)
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
      setHasSyncError(false)
      setIsSaving(true)
    } else {
      const elapsed = Date.now() - (savingStartTimeRef.current || 0)
      const remainingTime = Math.max(0, 500 - elapsed)

      setTimeout(() => {
        setIsSaving(false)
      }, remainingTime)
    }
  }

  const handleSyncError = () => {
    setHasSyncError(true)
    const now = Date.now()
    if (now - lastSyncErrorToastAtRef.current < SYNC_ERROR_TOAST_COOLDOWN_MS) {
      return
    }
    lastSyncErrorToastAtRef.current = now
    toast.error("Couldn't save document", {
      id: "notebook-sync-error",
      description:
        "Your latest edits could not be saved. Check your connection and try again.",
      duration: 8_000,
    })
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
      <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
        <div className="flex justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  if (!document) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
        <p className="py-16 text-center text-sm text-muted-foreground">
          Document not found
        </p>
      </div>
    )
  }

  const isReconnecting = wsStatus === "reconnecting"
  const isConnecting = wsStatus === "connecting"

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
      <header className="border-b pb-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0 flex-1">
            <EditableTitle
              title={document.name}
              onTitleChange={handleTitleChange}
              isLoading={updateDocumentMutation.isPending}
              size="lg"
              textAlign="left"
            />
          </div>
          <div
            className="flex shrink-0 items-center gap-1.5 text-xs text-muted-foreground"
            role="status"
            aria-live="polite"
          >
            {isReconnecting ? (
              <>
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-warning" />
                <span className="text-warning">Reconnecting...</span>
              </>
            ) : isConnecting ? (
              <>
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground/60" />
                <span>Connecting...</span>
              </>
            ) : isSaving ? (
              <>
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground/60" />
                <span>Syncing...</span>
              </>
            ) : isEditing ? (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60" />
                <span>Editing...</span>
              </>
            ) : hasSyncError ? (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
                <span className="text-destructive">Couldn't save</span>
              </>
            ) : (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                <span>Saved</span>
              </>
            )}
          </div>
        </div>
      </header>
      <div className="mt-2">
        <Suspense
          fallback={
            <div className="flex justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          }
        >
          <CollabEditor
            docId={documentId}
            legacyContent={document.content}
            onSavingChange={handleSavingChange}
            onEditingChange={setIsEditing}
            onConnectionChange={setWsStatus}
            onSyncError={handleSyncError}
          />
        </Suspense>
      </div>
    </div>
  )
}

function DocumentContent() {
  return <DocumentContentLoader />
}
