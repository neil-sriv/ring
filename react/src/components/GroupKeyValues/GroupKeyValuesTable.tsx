import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { Suspense, lazy, useRef, useState } from "react"
import type {
  FullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutError,
  GroupKeyValue,
} from "../../client"
import {
  fullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutMutation,
  readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

const ReactJson = lazy(() => import("react-json-view"))

type SaveStatus = "idle" | "saving" | "saved" | "error"

function GroupStoreSaveStatus({ status }: { status: SaveStatus }) {
  if (status === "idle") {
    return null
  }

  if (status === "saving") {
    return (
      <p
        className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground"
        role="status"
        aria-live="polite"
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Saving...
      </p>
    )
  }

  if (status === "error") {
    return (
      <p
        className="mt-2 text-sm text-destructive"
        role="status"
        aria-live="polite"
      >
        Couldn't save. Edit again to retry.
      </p>
    )
  }

  return (
    <p
      className="mt-2 text-sm text-muted-foreground"
      role="status"
      aria-live="polite"
    >
      Saved
    </p>
  )
}

export function GroupKeyValuesTable({
  keyValues,
  groupApiId,
}: {
  keyValues: GroupKeyValue
  groupApiId: string
}) {
  const [editableData, setEditableData] = useState(keyValues.key_values)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle")
  const showToast = useCustomToast()
  const queryClient = useQueryClient()

  // Full-replace PUTs must not overlap: an older in-flight response can
  // overwrite a newer edit. Keep the latest payload and flush once free.
  const latestPayloadRef = useRef(keyValues.key_values)
  const saveInFlightRef = useRef(false)
  const pendingFlushRef = useRef(false)

  const addKey = useMutation({
    ...fullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutMutation(),
    onSuccess: () => {
      if (!pendingFlushRef.current) {
        setSaveStatus("saved")
      }
    },
    onError: (
      err: AxiosError<FullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutError>,
    ) => {
      setSaveStatus("error")
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: (_data, error) => {
      queryClient.invalidateQueries({
        queryKey: readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey({
          path: { group_api_id: groupApiId },
        }),
      })
      saveInFlightRef.current = false
      if (!error && pendingFlushRef.current) {
        pendingFlushRef.current = false
        flushLatest()
      } else if (error) {
        pendingFlushRef.current = false
      }
    },
  })

  function flushLatest() {
    if (saveInFlightRef.current) {
      pendingFlushRef.current = true
      return
    }
    saveInFlightRef.current = true
    setSaveStatus("saving")
    addKey.mutate({
      path: { group_api_id: groupApiId },
      body: {
        key_values: latestPayloadRef.current,
      },
    })
  }

  const handleEdit = ({ updated_src }: { updated_src: any }) => {
    setEditableData(updated_src)
    latestPayloadRef.current = updated_src
    flushLatest()
  }

  return (
    <div className="w-full">
      <h3 className="text-base font-semibold">Group Store</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Use this as a fast data store for the group.
      </p>
      <GroupStoreSaveStatus status={saveStatus} />
      <div className="mt-4 overflow-x-auto rounded-lg border">
        <Suspense
          fallback={
            <div className="p-4 text-sm text-muted-foreground">
              Loading editor...
            </div>
          }
        >
          <ReactJson
            src={editableData}
            onEdit={handleEdit}
            onAdd={handleEdit}
            onDelete={handleEdit}
            theme="monokai"
            enableClipboard={false}
            displayDataTypes={false}
            collapsed={false}
            name={false}
            style={{ padding: "1rem" }}
          />
        </Suspense>
      </div>
    </div>
  )
}
