import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  AddMembersPartiesGroupGroupApiIdAddMembersPostError,
  GroupLinked,
  UserLinked,
} from "../../client"
import {
  addMembersPartiesGroupGroupApiIdAddMembersPostMutation,
  listGroupsPartiesGroupsGetQueryKey,
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
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

interface AddMembersProps {
  group: GroupLinked
  isOpen: boolean
  onClose: () => void
}

type AddMembersFormType = {
  member_emails: string
}

const AddMembers = ({ group, isOpen, onClose }: AddMembersProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<AddMembersFormType>({
    mode: "onBlur",
    criteriaMode: "all",
  })

  const mutation = useMutation({
    ...addMembersPartiesGroupGroupApiIdAddMembersPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Group updated successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      err: AxiosError<AddMembersPartiesGroupGroupApiIdAddMembersPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: group.api_identifier },
        }),
      })
      if (currentUser) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser.api_identifier },
          }),
        })
      }
    },
  })

  const onSubmit: SubmitHandler<AddMembersFormType> = async (data) => {
    const memberEmails = data.member_emails
      .split(",")
      .map((email) => email.trim())
    mutation.mutate({
      body: { member_emails: memberEmails },
      path: { group_api_id: group.api_identifier },
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
            <DialogTitle>Add new members</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-2">
              <Label htmlFor="name">New Member Emails</Label>
              <p className="text-sm text-muted-foreground">
                Enter the email addresses of the new members you want to add to
                this group. Separate multiple emails with a comma.
              </p>
              <Input
                id="name"
                {...register("member_emails", {
                  required: "New member emails are required",
                })}
                type="text"
              />
              {errors.member_emails && (
                <p className="text-sm text-destructive">
                  {errors.member_emails.message}
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

export default AddMembers
