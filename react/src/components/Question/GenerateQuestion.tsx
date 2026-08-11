import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import type {
  AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
  UserLinked,
} from "../../client"
import {
  addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
  generateQuestionLettersLetterLetterApiIdGenerateQuestionPostMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

type QuestionFormProps = {
  questionPrompt: string
}

interface GenerateQuestionProps {
  isOpen: boolean
  onClose: () => void
  loopApiId: string
}

const GenerateQuestion = ({
  isOpen,
  onClose,
  loopApiId,
}: GenerateQuestionProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const router = useRouter()
  const showToast = useCustomToast()
  const [generatedQuestion, setGeneratedQuestion] = useState<string>("")
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<QuestionFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
  })

  const generateQuestionMutation = useMutation({
    ...generateQuestionLettersLetterLetterApiIdGenerateQuestionPostMutation({
      path: { letter_api_id: loopApiId },
    }),
    onSuccess: (data) => {
      setGeneratedQuestion(data.generated_text)
      showToast("Success!", "Question generated successfully.", "success")
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
  })

  const addQuestionMutation = useMutation({
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

  const onGenerateQuestion: SubmitHandler<QuestionFormProps> = (data) => {
    generateQuestionMutation.mutate({
      body: {
        prompt: data.questionPrompt,
      },
      path: { letter_api_id: loopApiId },
    })
  }

  const onSaveQuestion = () => {
    if (!generatedQuestion) {
      showToast(
        "Error",
        "No question to save. Please generate a question first.",
        "error",
      )
      return
    }

    addQuestionMutation.mutate({
      body: {
        question_text: generatedQuestion,
        author_api_id: currentUser?.api_identifier || null,
      },
      path: { letter_api_id: loopApiId },
    })
  }

  const handleClose = () => {
    reset()
    setGeneratedQuestion("")
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 sm:max-w-md">
        <form onSubmit={handleSubmit(onGenerateQuestion)}>
          <DialogHeader>
            <DialogTitle className="text-foreground">
              Generate question
            </DialogTitle>
            <DialogDescription className="sr-only">
              Generate a question using AI
            </DialogDescription>
          </DialogHeader>
          <div className="pb-6 pt-4 space-y-4">
            <div>
              <Textarea
                id="questionPrompt"
                placeholder="Enter a prompt to generate a question..."
                {...register("questionPrompt", {
                  required: "Question prompt is required.",
                })}
                className="min-h-[100px] bg-white/50 border-white/20 dark:bg-gray-900/50 dark:border-gray-700/50 hover:border-primary focus-visible:border-primary focus-visible:ring-primary"
              />
              {errors.questionPrompt && (
                <p className="text-sm text-destructive mt-1">
                  {errors.questionPrompt.message}
                </p>
              )}
            </div>
            {generatedQuestion && (
              <div>
                <Textarea
                  id="generatedQuestion"
                  value={generatedQuestion}
                  readOnly
                  placeholder="Generated question will appear here..."
                  className="min-h-[100px] bg-white/50 border-white/20 dark:bg-gray-900/50 dark:border-gray-700/50"
                />
              </div>
            )}
          </div>

          <DialogFooter className="gap-3">
            <Button type="submit" disabled={generateQuestionMutation.isPending}>
              {generateQuestionMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Generate
            </Button>
            <Button
              type="button"
              onClick={onSaveQuestion}
              disabled={addQuestionMutation.isPending || !generatedQuestion}
              variant="outline"
            >
              {addQuestionMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default GenerateQuestion
