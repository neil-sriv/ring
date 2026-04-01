import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  CreateGroupPartiesGroupPostError,
  GroupCreate,
  UserLinked,
} from "../../client"
import {
  createGroupPartiesGroupPostMutation,
  listGroupsPartiesGroupsGetQueryKey,
  readUserMePartiesMeGetQueryKey,
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

interface AddGroupProps {
  isOpen: boolean
  onClose: () => void
}

const AddGroup = ({ isOpen, onClose }: AddGroupProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GroupCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
    },
  })

  const mutation = useMutation({
    ...createGroupPartiesGroupPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Group created successfully.", "success")
      reset()
      onClose()
    },
    onError: (err: AxiosError<CreateGroupPartiesGroupPostError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: (data) => {
      if (data) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser!.api_identifier },
          }),
        })
      }
    },
  })

  const onSubmit: SubmitHandler<GroupCreate> = (data) => {
    mutation.mutate({
      body: {
        admin_api_identifier: currentUser!.api_identifier,
        name: data.name,
      },
    })
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
            <DialogTitle>Add Group</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required.",
                })}
                placeholder="Name"
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
            <Button variant="outline" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddGroup
