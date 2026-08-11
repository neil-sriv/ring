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
import type { AddNextLetterLettersLetterPostError } from "../../client"
import {
  addNextLetterLettersLetterPostMutation,
  listLettersLettersLettersGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import {
  defaultLocalDateTimeValue,
  formatApiErrorDetail,
  toISOLocal,
} from "../../util/misc"

type LetterFormProps = {
  sendAt: Date | string
}

interface AddLetterProps {
  isOpen: boolean
  onClose: () => void
  groupApiId: string
}

const AddLetter = ({ isOpen, onClose, groupApiId }: AddLetterProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<LetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      sendAt: defaultLocalDateTimeValue(14),
    },
  })

  const mutation = useMutation({
    ...addNextLetterLettersLetterPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Next letter created successfully.", "success")
      reset()
      onClose()
    },
    onError: (err: AxiosError<AddNextLetterLettersLetterPostError>) => {
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

  const onSubmit: SubmitHandler<LetterFormProps> = (data) => {
    mutation.mutate({
      body: {
        group_api_identifier: groupApiId,
        send_at:
          data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt,
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
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Start Next Loop</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
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

export default AddLetter
