import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  GroupLinked,
  GroupUpdate,
  UpdateGroupPartiesGroupGroupApiIdPatchError,
  UserLinked,
} from "../../client"
import {
  listGroupsPartiesGroupsGetQueryKey,
  readUserMePartiesMeGetQueryKey,
  updateGroupPartiesGroupGroupApiIdPatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface EditGroupProps {
  group: GroupLinked
  isOpen: boolean
  onClose: () => void
}

const EditGroup = ({ group, isOpen, onClose }: EditGroupProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<GroupUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group.name,
    },
  })

  // ActionsMenu keeps this dialog mounted; re-sync when opened or group changes.
  useEffect(() => {
    if (isOpen) {
      reset({ name: group.name })
    }
  }, [isOpen, group.name, reset])

  const mutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
    onSuccess: (_data, variables) => {
      showToast("Success!", "Group updated successfully.", "success")
      reset({ name: variables.body.name ?? group.name })
      onClose()
    },
    onError: (err: AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: listGroupsPartiesGroupsGetQueryKey({
          query: { user_api_id: currentUser!.api_identifier },
        }),
      })
    },
  })

  const onSubmit: SubmitHandler<GroupUpdate> = async (data) => {
    mutation.mutate({
      path: { group_api_id: group.api_identifier },
      body: data,
    })
  }

  const onCancel = () => {
    reset({ name: group.name })
    onClose()
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onCancel()
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Group</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required",
                })}
                type="text"
              />
              {errors.name && (
                <p className="text-xs text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={onCancel} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !isDirty}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default EditGroup
