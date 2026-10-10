import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type {
  GroupUpdate,
  UpdateGroupPartiesGroupGroupApiIdPatchError,
  UserLinked,
} from "../../client"
import {
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listGroupsPartiesGroupsGetQueryKey,
  listLettersLettersLettersGetQueryKey,
  readGroupPartiesGroupGroupApiIdGetOptions,
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readUserMePartiesMeGetOptions,
  readUserMePartiesMeGetQueryKey,
  updateGroupPartiesGroupGroupApiIdPatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

function GroupInformation({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const router = useRouter()
  const [editMode, setEditMode] = useState(false)
  // Subscribe to the group query so cache writes (e.g. Edit Group rename via
  // setQueryData) re-render this view. getQueryData alone never re-renders.
  const { data: group } = useQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupId },
    }),
  })
  // Live /me for listGroups invalidation keys after rename.
  const { data: currentUser } = useQuery({
    ...readUserMePartiesMeGetOptions(),
  })

  // Hooks must run unconditionally — never after the group early-return below.
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, isDirty, errors },
  } = useForm<GroupUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group?.name ?? "",
    },
  })

  useEffect(() => {
    if (!group || editMode) {
      return
    }
    reset({ name: group.name })
  }, [group, editMode, reset])

  const mutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
  })

  if (group === undefined) {
    return null
  }

  const refreshCaches = async (updatedName: string) => {
    // Settings uses ensureQueryData in beforeLoad; write the new name so the
    // next visit (and this view) show the PATCH result immediately.
    queryClient.setQueryData(
      readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: groupId },
      }),
      { ...group, name: updatedName },
    )
    queryClient.setQueryData<UserLinked>(
      readUserMePartiesMeGetQueryKey(),
      (previous) => {
        if (!previous) {
          return previous
        }
        return {
          ...previous,
          groups: previous.groups.map((entry) =>
            entry.api_identifier === groupId
              ? { ...entry, name: updatedName }
              : entry,
          ),
        }
      },
    )
    if (currentUser) {
      queryClient.invalidateQueries({
        queryKey: listGroupsPartiesGroupsGetQueryKey({
          query: { user_api_id: currentUser.api_identifier },
        }),
      })
    }
    queryClient.invalidateQueries({
      queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: groupId },
      }),
    })
    queryClient.invalidateQueries({
      queryKey: readUserMePartiesMeGetQueryKey(),
    })
    // Home cards embed loop.group.name from dashboard list (30s staleTime).
    queryClient.invalidateQueries({
      queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
    })
    queryClient.invalidateQueries({
      queryKey: listLettersLettersLettersGetQueryKey({
        query: { group_api_id: groupId },
      }),
    })
    router.invalidate()
  }

  const onSubmit: SubmitHandler<GroupUpdate> = async (data) => {
    const nextName = data.name?.trim() ?? ""
    try {
      const updated = await mutation.mutateAsync({
        path: { group_api_id: groupId },
        body: { name: nextName },
      })
      showToast(
        "Success!",
        "Group information updated successfully.",
        "success",
      )
      reset({ name: updated.name })
      setEditMode(false)
      await refreshCaches(updated.name)
    } catch (err) {
      const axiosErr =
        err as AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(axiosErr.response?.data?.detail),
        "error",
      )
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
            <Label htmlFor="group-information-name">Name</Label>
            {editMode ? (
              <Input
                id="group-information-name"
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
            onClick={editMode ? undefined : () => setEditMode(true)}
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
