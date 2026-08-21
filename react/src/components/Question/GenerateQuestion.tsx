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
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2, Sparkles } from "lucide-react"
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
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onGenerateQuestion)}>
          <DialogHeader>
            <DialogTitle>Generate question</DialogTitle>
            <DialogDescription className="sr-only">
              Generate a question using AI
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-5 pb-6 pt-4">
            <div className="grid gap-1.5">
              <Label htmlFor="questionPrompt">Prompt</Label>
              <Textarea
                id="questionPrompt"
                placeholder="Enter a prompt to generate a question..."
                {...register("questionPrompt", {
                  required: "Question prompt is required.",
                })}
                className="min-h-[100px]"
              />
              {errors.questionPrompt && (
                <p className="text-xs text-destructive">
                  {errors.questionPrompt.message}
                </p>
              )}
            </div>
            {generatedQuestion && (
              <div className="rounded-lg border bg-muted/50 px-4 py-3">
                <p className="text-xs text-muted-foreground">
                  Generated question
                </p>
                <p className="mt-1 font-display text-base font-medium leading-relaxed">
                  {generatedQuestion}
                </p>
              </div>
            )}
          </div>

          <DialogFooter className="gap-3">
            <Button type="submit" disabled={generateQuestionMutation.isPending}>
              {generateQuestionMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
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
