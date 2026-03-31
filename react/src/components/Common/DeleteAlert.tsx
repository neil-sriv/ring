import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { useMutation } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"

// import { LettersService, PartiesService } from "../../client";
import useCustomToast from "../../hooks/useCustomToast"

interface DeleteProps {
  type: string
  id: string
  isOpen: boolean
  onClose: () => void
}

const Delete = ({ type, isOpen, onClose }: DeleteProps) => {
  // const queryClient = useQueryClient();
  const showToast = useCustomToast()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteEntity = async () => {
    throw new Error("Not implemented")
    // if (type === "Item") {
    //   await LettersService.readLetterLettersLetterLetterApiIdGet({
    //     letterApiId: id,
    //   });
    // } else if (type === "User") {
    //   await PartiesService.deleteUserPartiesUserIdDelete({ userId: id });
    // } else {
    //   throw new Error(`Unexpected type: ${type}`);
    // }
  }

  const mutation = useMutation({
    mutationFn: deleteEntity,
    onSuccess: () => {
      showToast(
        "Success",
        `The ${type.toLowerCase()} was deleted successfully.`,
        "success",
      )
      onClose()
    },
    onError: () => {
      showToast(
        "An error occurred.",
        `An error occurred while deleting the ${type.toLowerCase()}.`,
        "error",
      )
    },
    onSettled: () => {
      // const queryKey =
      //   type === "Group" ? readGroupPartiesGroupGroupApiIdGetQueryKey({path: {group_api_id: }}) : readUsersPartiesUsersGetQueryKey();
      // queryClient.invalidateQueries({
      //   queryKey: [type === "Group" ? "groups" : "users"],
      // });
    },
  })

  const onSubmit = async () => {
    mutation.mutate()
  }

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
            <AlertDialogTitle>Delete {type}</AlertDialogTitle>
            <AlertDialogDescription>
              {type === "User" && (
                <span>
                  All items associated with this user will also be{" "}
                  <strong>permantly deleted. </strong>
                </span>
              )}
              Are you sure? You will not be able to undo this action.
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
              Delete
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default Delete
