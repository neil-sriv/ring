import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
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

function cloneKeyValues(value: Record<string, unknown>) {
  return structuredClone(value)
}

export function GroupKeyValuesTable({
  keyValues,
  groupApiId,
}: {
  keyValues: GroupKeyValue
  groupApiId: string
}) {
  const [editableData, setEditableData] = useState(() =>
    cloneKeyValues(keyValues.key_values),
  )
  // Last successfully persisted snapshot — used to roll back optimistic edits
  // when a full-replace PUT fails (otherwise the editor stays out of sync).
  const lastSavedRef = useRef(cloneKeyValues(keyValues.key_values))
  // Full-replace PUTs are not serialized, so an older attempt can settle after
  // a newer one. `saveGenerationRef` is the newest attempt started,
  // `lastSuccessGenRef` the newest that succeeded, and `inFlightRef` how many
  // are still outstanding.
  const saveGenerationRef = useRef(0)
  const lastSuccessGenRef = useRef(0)
  const inFlightRef = useRef(0)
  // react-json-view ignores later `src` changes; bump key on rollback to remount.
  const [editorKey, setEditorKey] = useState(0)
  const showToast = useCustomToast()
  const queryClient = useQueryClient()

  const addKey = useMutation({
    ...fullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutMutation(),
    onSuccess: () => {
      showToast("Success!", "Key value updated.", "success")
    },
    onError: (
      err: AxiosError<FullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey({
          path: { group_api_id: groupApiId },
        }),
      })
    },
  })

  const handleEdit = ({ updated_src }: { updated_src: any }) => {
    const generation = ++saveGenerationRef.current
    inFlightRef.current += 1
    setEditableData(updated_src)
    addKey.mutate(
      {
        path: { group_api_id: groupApiId },
        body: {
          key_values: updated_src,
        },
      },
      {
        onSuccess: () => {
          // Compare against the newest *success*, not the newest attempt: a
          // save that lands while a later one is still in flight is still the
          // freshest thing on the server, and skipping it here would leave the
          // snapshot behind for a subsequent rollback to restore.
          if (generation < lastSuccessGenRef.current) {
            return
          }
          lastSuccessGenRef.current = generation
          lastSavedRef.current = cloneKeyValues(updated_src)

          // This success arrived after a newer attempt, which may already have
          // rolled the editor back to an older snapshot. Once nothing else is
          // outstanding, repaint so the tree matches what was persisted.
          if (
            generation !== saveGenerationRef.current &&
            inFlightRef.current <= 1
          ) {
            setEditableData(cloneKeyValues(lastSavedRef.current))
            setEditorKey((key) => key + 1)
          }
        },
        onError: () => {
          // Rolling back a superseded attempt would show stale values while a
          // newer edit is still in flight (or has already landed).
          if (generation !== saveGenerationRef.current) {
            return
          }
          setEditableData(cloneKeyValues(lastSavedRef.current))
          setEditorKey((key) => key + 1)
        },
        onSettled: () => {
          inFlightRef.current -= 1
        },
      },
    )
  }

  return (
    <div className="w-full">
      <h3 className="text-base font-semibold">Group Store</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Use this as a fast data store for the group.
      </p>
      <div className="mt-4 overflow-x-auto rounded-lg border">
        <Suspense
          fallback={
            <div className="p-4 text-sm text-muted-foreground">
              Loading editor...
            </div>
          }
        >
          <ReactJson
            key={editorKey}
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
