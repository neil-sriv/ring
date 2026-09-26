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
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listLettersLettersLettersGetQueryKey,
  readLetterLettersLetterLetterApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail, toISOLocal } from "../../util/misc"

type LetterFormProps = {
  // datetime-local values are always strings ("YYYY-MM-DDTHH:mm"). Do not use
  // react-hook-form's valueAsDate here: it desyncs from the controlled `values`
  // string and falsely fails `required` until the user re-picks the date.
  sendAt: string
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
  const previousSendAtLocal = toISOLocal(previousSendAt).slice(0, 16)
  // Allow the letter's existing send_at even when it is already in the past
  // (common for IN_PROGRESS); otherwise the browser marks the field invalid
  // and status-only saves fail until the user re-picks a future time.
  const sendAtMin = toISOLocal(
    new Date(Math.min(Date.now(), previousSendAt.getTime())),
  ).slice(0, 16)
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
          sendAt: previousSendAtLocal,
          title: loop.title || "",
          isInProgress: loop.status === "IN_PROGRESS",
        }
      : undefined,
  })

  const mutation = useMutation({
    ...editLetterLettersLetterLetterApiIdEditLetterPostMutation(),
    onSuccess: (data) => {
      // Keep detail warm so the open loop page reflects the save immediately.
      queryClient.setQueryData(
        readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
        data,
      )
      showToast("Success!", "Letter updated successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      err: AxiosError<EditLetterLettersLetterLetterApiIdEditLetterPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
      })
      // Group Loops / dashboard cards use list queries with a 30s staleTime;
      // without this, renamed titles stay wrong until the cache expires.
      queryClient.invalidateQueries({
        queryKey: listLettersLettersLettersGetQueryKey({
          query: { group_api_id: loop.group.api_identifier },
        }),
      })
      queryClient.invalidateQueries({
        queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<LetterFormProps> = async (data) => {
    const updateData: {
      send_at?: string
      title?: string
      status?: LetterStatus
    } = {}

    // Compare minute-precision local strings so an unchanged datetime-local
    // value does not count as a change. Convert to timezone-aware ISO only
    // when the user actually changed the scheduled time.
    const nextSendAtLocal = data.sendAt.slice(0, 16)

    if (nextSendAtLocal !== previousSendAtLocal) {
      updateData.send_at = toISOLocal(new Date(data.sendAt))
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
      await mutation.mutateAsync({
        body: updateData,
        path: { letter_api_id: loop.api_identifier },
      })
    } else {
      showToast("No changes", "No changes were made to the letter.", "success")
      onClose()
    }
  }

  const isSaving = isSubmitting || mutation.isPending

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open && !isSaving) onClose()
      }}
    >
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Loop</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                {...register("title")}
                placeholder="Enter letter title"
                disabled={isSaving}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="isInProgress">Status</Label>
              <div className="flex items-center gap-4">
                <span
                  className={`text-sm ${
                    !watch("isInProgress")
                      ? "font-medium text-foreground"
                      : "text-muted-foreground"
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
                    disabled={isSaving}
                  />
                  <div className="peer h-6 w-11 rounded-full bg-muted after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-border after:bg-background after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-focus:ring-2 peer-focus:ring-ring peer-disabled:cursor-not-allowed peer-disabled:opacity-50" />
                </label>
                <span
                  className={`text-sm ${
                    watch("isInProgress")
                      ? "font-medium text-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  In Progress
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sendAt">
                Send at <span className="text-destructive">*</span>
              </Label>
              <Input
                id="sendAt"
                {...register("sendAt", {
                  required: "Send at is required.",
                })}
                type="datetime-local"
                min={sendAtMin}
                disabled={isSaving}
              />
              {errors.sendAt && (
                <p className="text-xs text-destructive">
                  {errors.sendAt.message}
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSaving}
            >
              Cancel
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default EditLetter
