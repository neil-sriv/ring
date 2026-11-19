import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
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
import type { AddNextLetterLettersLetterPostError } from "../../client"
import {
  addNextLetterLettersLetterPostMutation,
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listLettersLettersLettersGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { useSubmitOnce } from "../../hooks/useSubmitOnce"
import {
  defaultLocalDateTimeValue,
  formatApiErrorDetail,
  toISOLocal,
} from "../../util/misc"

// Axios leaves timeout at 0, so a hung create never rejects and isSaving stays
// true. This write is a small JSON body; uploads keep the longer proxy window.
const ADD_LETTER_TIMEOUT_MS = 20_000

type LetterFormProps = {
  // datetime-local values are always strings ("YYYY-MM-DDTHH:mm"). Do not use
  // react-hook-form's valueAsDate here: it desyncs from string defaults and can
  // falsely fail `required`, or submit a bare local string without a timezone.
  sendAt: string
}

interface AddLetterProps {
  isOpen: boolean
  onClose: () => void
  groupApiId: string
}

const freshDefaults = (): LetterFormProps => ({
  sendAt: defaultLocalDateTimeValue(14),
})

const AddLetter = ({ isOpen, onClose, groupApiId }: AddLetterProps) => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<LetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: freshDefaults(),
  })

  // Parent keeps this dialog mounted; recompute send-at defaults each open.
  useEffect(() => {
    if (isOpen) {
      reset(freshDefaults())
    }
  }, [isOpen, reset])

  const mutation = useMutation({
    ...addNextLetterLettersLetterPostMutation(),
    onSuccess: (letter) => {
      showToast("Success!", "Next letter created successfully.", "success")
      reset(freshDefaults())
      onClose()
      void navigate({
        to: "/loops/$loopId",
        params: { loopId: letter.api_identifier },
      })
    },
    onError: (err: AxiosError<AddNextLetterLettersLetterPostError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      // Group Loops list + Home dashboard both use 30s staleTime; without
      // dashboard invalidation a soft-nav to Home keeps the pre-create cards.
      queryClient.invalidateQueries({
        queryKey: listLettersLettersLettersGetQueryKey({
          query: { group_api_id: groupApiId },
        }),
      })
      queryClient.invalidateQueries({
        queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
      })
    },
  })

  const submitOnce = useSubmitOnce()
  const isSaving = isSubmitting || mutation.isPending || submitOnce.pending

  const onSubmit: SubmitHandler<LetterFormProps> = async (data) => {
    await submitOnce.run(async () => {
      try {
        await mutation.mutateAsync({
          body: {
            group_api_identifier: groupApiId,
            send_at: toISOLocal(new Date(data.sendAt)),
          },
          timeout: ADD_LETTER_TIMEOUT_MS,
        })
      } catch {
        // onError already toasts. Swallow so handleSubmit clears isSubmitting.
      }
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
        if (!open && !isSaving) onCancel()
      }}
    >
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Start Next Loop</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
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
                min={toISOLocal(new Date()).slice(0, 16)}
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
              onClick={onCancel}
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

export default AddLetter
