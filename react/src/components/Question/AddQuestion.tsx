import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import type {
  AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
  UserLinked,
} from "../../client"
import {
  addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

type QuestionFormProps = {
  questionText: string
}

interface AddQuestionProps {
  isOpen: boolean
  onClose: () => void
  loopApiId: string
}

const AddQuestion = ({ isOpen, onClose, loopApiId }: AddQuestionProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const router = useRouter()
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<QuestionFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
  })

  const mutation = useMutation({
    ...addQuestionLettersLetterLetterApiIdAddQuestionPostMutation(),
    onSuccess: () => {
      showToast("Success!", "New question created successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      err: AxiosError<AddQuestionLettersLetterLetterApiIdAddQuestionPostError>,
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
          path: { letter_api_id: loopApiId },
        }),
      })
      router.invalidate()
    },
  })

  const onSubmit: SubmitHandler<QuestionFormProps> = (data) => {
    mutation.mutate({
      body: {
        question_text: data.questionText,
        author_api_id: currentUser!.api_identifier,
      },
      path: { letter_api_id: loopApiId },
    })
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add new question</DialogTitle>
            <DialogDescription className="sr-only">
              Add a new question to the loop
            </DialogDescription>
          </DialogHeader>
          <div className="pb-6 pt-4">
            <div className="grid gap-1.5">
              <Label htmlFor="questionText">Question</Label>
              <Textarea
                id="questionText"
                {...register("questionText", {
                  required: "Question text is required.",
                })}
                className="min-h-[100px]"
                placeholder="Enter your question here..."
              />
              {errors.questionText && (
                <p className="text-xs text-destructive">
                  {errors.questionText.message}
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-3">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save
            </Button>
            <Button type="button" onClick={onClose} variant="outline">
              Cancel
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddQuestion
