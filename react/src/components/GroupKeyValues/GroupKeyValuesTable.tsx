import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useState } from "react"
import ReactJson from "react-json-view"
import type {
  FullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutError,
  GroupKeyValue,
} from "../../client"
import {
  fullReplaceGroupKeyValuesPartiesGroupGroupApiIdKeyValuePutMutation,
  readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"

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
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
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
    <div className="w-full flex flex-col gap-4">
      <p>Group Key Values; use this as a fast data store for the group.</p>(
      <div className="border border-gray-200 rounded-md p-4">
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
        />
      </div>
      )
    </div>
  )
}
