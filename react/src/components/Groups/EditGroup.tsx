import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
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
    defaultValues: group,
  })

  const mutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "Group updated successfully.", "success")
      reset()
      onClose()
    },
    onError: (err: AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
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
    reset()
    onClose()
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Group</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required",
                })}
                type="text"
              />
              {errors.name && (
                <p className="text-sm text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>
            {/* <div className="mt-4 space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                {...register("description")}
                placeholder="Description"
                type="text"
              />
            </div> */}
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
