import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type {
  GroupLinked,
  GroupUpdate,
  UpdateGroupPartiesGroupGroupApiIdPatchError,
} from "../../client"
import {
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  updateGroupPartiesGroupGroupApiIdPatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

function GroupInformation({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const router = useRouter()
  const [editMode, setEditMode] = useState(false)
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    }),
  )
  if (group === undefined) {
    return null
  }

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, isDirty, errors },
  } = useForm<GroupUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group.name,
    },
  })

  const mutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
  })

  const refreshGroup = async () => {
    queryClient.invalidateQueries({
      queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: groupId },
      }),
    })
    router.invalidate()
    await queryClient.refetchQueries({
      queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: groupId },
      }),
    })
  }

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const onSubmit: SubmitHandler<GroupUpdate> = async (data) => {
    try {
      await mutation.mutateAsync({
        path: { group_api_id: groupId },
        body: { name: data.name },
      })
      showToast(
        "Success!",
        "Group information updated successfully.",
        "success",
      )
      setEditMode(false)
      reset({ name: data.name })
    } catch (err) {
      const axiosErr =
        err as AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(axiosErr.response?.data?.detail),
        "error",
      )
    } finally {
      await refreshGroup()
    }
  }

  const onCancel = () => {
    reset({ name: group.name })
    setEditMode(false)
  }

  const isSaving = isSubmitting || mutation.isPending

  return (
    <div className="w-full max-w-xl">
      <h3 className="text-base font-semibold">Group Information</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        The basics of this group.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6">
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Name</Label>
            {editMode ? (
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required",
                  maxLength: {
                    value: 30,
                    message: "Name must be at most 30 characters",
                  },
                })}
                type="text"
              />
            ) : (
              <p className="text-sm">{group.name || "N/A"}</p>
            )}
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Created At</Label>
            <p className="text-sm">
              {new Date(group.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="mt-6 flex gap-3 border-t pt-6">
          <Button
            onClick={editMode ? undefined : toggleEditMode}
            type={editMode ? "submit" : "button"}
            disabled={editMode ? !isDirty || isSaving : false}
          >
            {editMode && isSaving && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {editMode ? "Save" : "Edit"}
          </Button>
          {editMode && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSaving}
            >
              Cancel
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}

export default GroupInformation
