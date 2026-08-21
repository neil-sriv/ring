import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"

import type {
  RemoveUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPostError,
  UserLinked,
  UserUnlinked,
} from "../../client"
import {
  listGroupsPartiesGroupsGetQueryKey,
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
  removeUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPostMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

interface RemoveMemberConfirmationProps {
  groupId: string
  member: UserUnlinked
  isOpen: boolean
  onClose: () => void
}

function RemoveMemberConfirmation({
  groupId,
  member,
  isOpen,
  onClose,
}: RemoveMemberConfirmationProps) {
  const queryClient = useQueryClient()
  const router = useRouter()
  const showToast = useCustomToast()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const mutation = useMutation({
    ...removeUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPostMutation(),
    onSuccess: () => {
      showToast(
        "Success!",
        `${member.name || member.email} was removed from the group.`,
        "success",
      )
      onClose()
    },
    onError: (
      err: AxiosError<RemoveUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: async () => {
      queryClient.invalidateQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: groupId },
        }),
      })
      if (currentUser) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser.api_identifier },
          }),
        })
      }
      router.invalidate()
      await queryClient.refetchQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: groupId },
        }),
      })
    },
  })

  const onSubmit = async () => {
    mutation.mutate({
      path: {
        group_api_id: groupId,
        user_api_id: member.api_identifier,
      },
    })
  }

  const memberLabel = member.name || member.email

  return (
    <AlertDialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <AlertDialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove member?</AlertDialogTitle>
            <AlertDialogDescription>
              <span className="font-medium text-foreground">
                {memberLabel}
              </span>{" "}
              will be removed from this group. They will no longer receive new
              loops or be able to access group content. This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              type="button"
            >
              Cancel
            </Button>
            <Button variant="destructive" type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Remove
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default RemoveMemberConfirmation
