import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
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
import type { AddNextLetterLettersLetterLetterTypePostError } from "../../client"
import {
  addNextLetterLettersLetterLetterTypePostMutation,
  listLettersLettersLettersGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import {
  defaultLocalDateTimeValue,
  formatApiErrorDetail,
  toISOLocal,
} from "../../util/misc"

type AdhocLetterFormProps = {
  title: string
  sendAt: Date | string
}

type AddAdhocLoopProps = {
  isOpen: boolean
  onClose: () => void
  groupApiId: string
}

const freshDefaults = (): AdhocLetterFormProps => ({
  title: "",
  sendAt: defaultLocalDateTimeValue(7),
})

const AddAdhocLoop = ({ isOpen, onClose, groupApiId }: AddAdhocLoopProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AdhocLetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: freshDefaults(),
  })

  // Parent keeps this dialog mounted; clear title and refresh send-at each open.
  useEffect(() => {
    if (isOpen) {
      reset(freshDefaults())
    }
  }, [isOpen, reset])

  const mutation = useMutation({
    ...addNextLetterLettersLetterLetterTypePostMutation(),
    onSuccess: () => {
      showToast("Success!", "Adhoc loop created successfully.", "success")
      reset(freshDefaults())
      onClose()
    },
    onError: (
      err: AxiosError<AddNextLetterLettersLetterLetterTypePostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: listLettersLettersLettersGetQueryKey({
          query: { group_api_id: groupApiId },
        }),
      })
    },
  })

  const onSubmit: SubmitHandler<AdhocLetterFormProps> = (data) => {
    mutation.mutate({
      path: { letter_type: "ADHOC" },
      body: {
        group_api_identifier: groupApiId,
        send_at:
          data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt,
        title: data.title || null,
      },
    })
  }

  const onCancel = () => {
    reset(freshDefaults())
    onClose()
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onCancel()
      }}
    >
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create Adhoc Loop</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="title">Title (Optional)</Label>
              <Input
                id="title"
                {...register("title", {
                  maxLength: {
                    value: 100,
                    message: "Title must be less than 100 characters",
                  },
                })}
                placeholder="Enter a title for this adhoc loop"
              />
              {errors.title && (
                <p className="text-xs text-destructive">
                  {errors.title.message}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
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
                <p className="text-xs text-destructive">
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
              Create Adhoc Loop
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddAdhocLoop
