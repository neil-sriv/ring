import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Suspense, lazy, useState } from "react"
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

export function GroupKeyValuesTable({
  keyValues,
  groupApiId,
}: {
  keyValues: GroupKeyValue
  groupApiId: string
}) {
  const [editableData, setEditableData] = useState(keyValues.key_values)
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
    setEditableData(updated_src)
    addKey.mutate({
      path: { group_api_id: groupApiId },
      body: {
        key_values: updated_src,
      },
    })
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
