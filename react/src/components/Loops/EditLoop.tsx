import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

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
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import type {
  EditLetterLettersLetterLetterApiIdEditLetterPostError,
  LetterStatus,
  PublicLetter,
} from "../../client"
import {
  editLetterLettersLetterLetterApiIdEditLetterPostMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { toISOLocal } from "../../util/misc"

type LetterFormProps = {
  sendAt: Date | string
  title: string
  isInProgress: boolean
}

interface EditLetterProps {
  isOpen: boolean
  onClose: () => void
  loop: PublicLetter
}

const EditLetter = ({ isOpen, onClose, loop }: EditLetterProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const previousSendAt = new Date(loop.send_at)
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    values: isOpen
      ? {
          sendAt: toISOLocal(new Date(loop.send_at)).slice(0, 16),
          title: loop.title || "",
          isInProgress: loop.status === "IN_PROGRESS",
        }
      : undefined,
  })

  const mutation = useMutation({
    ...editLetterLettersLetterLetterApiIdEditLetterPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Letter updated successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      err: AxiosError<EditLetterLettersLetterLetterApiIdEditLetterPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
      })
    },
  })

  const onSubmit: SubmitHandler<LetterFormProps> = (data) => {
    const updateData: {
      send_at?: string
      title?: string
      status?: LetterStatus
    } = {}

    // Only include fields that have changed
    if (
      data.sendAt instanceof Date
        ? toISOLocal(data.sendAt)
        : data.sendAt !== toISOLocal(previousSendAt).slice(0, 16)
    ) {
      updateData.send_at =
        data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt
    }

    if (data.title !== (loop.title || "")) {
      updateData.title = data.title || undefined
    }

    const newStatus = data.isInProgress ? "IN_PROGRESS" : "UPCOMING"
    if (newStatus !== loop.status) {
      updateData.status = newStatus
    }

    // Only submit if there are changes
    if (Object.keys(updateData).length > 0) {
      mutation.mutate({
        body: updateData,
        path: { letter_api_id: loop.api_identifier },
      })
    } else {
      showToast("No changes", "No changes were made to the letter.", "success")
      onClose()
    }
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Loop</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                {...register("title")}
                placeholder="Enter letter title"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="isInProgress">Status</Label>
              <div className="flex items-center gap-4">
                <span
                  className={`text-sm ${
                    !watch("isInProgress")
                      ? "font-bold opacity-100"
                      : "font-normal opacity-60"
                  }`}
                >
                  Upcoming
                </span>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    id="isInProgress"
                    {...register("isInProgress")}
                    className="peer sr-only"
                  />
                  <div className="peer h-6 w-11 rounded-full bg-muted after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-border after:bg-background after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-focus:ring-2 peer-focus:ring-ring" />
                </label>
                <span
                  className={`text-sm ${
                    watch("isInProgress")
                      ? "font-bold opacity-100"
                      : "font-normal opacity-60"
                  }`}
                >
                  In Progress
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sendAt">
                Send at <span className="text-destructive">*</span>
              </Label>
              <Input
                id="sendAt"
                {...register("sendAt", {
                  required: "Send at is required.",
                  valueAsDate: true,
                })}
                type="datetime-local"
                min={toISOLocal(new Date()).slice(0, 16)}
              />
              {errors.sendAt && (
                <p className="text-sm text-destructive">
                  {errors.sendAt.message}
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save
            </Button>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default EditLetter
