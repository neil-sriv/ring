import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import {
  type PublicQuestion,
  type UpsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePostError,
  type UserLinked,
  upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost,
} from "../../client"
import {
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { useAutoResizeTextarea } from "../../hooks/useAutoResizeTextarea"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

interface LateAnswerQuestionProps {
  question: PublicQuestion
  loopApiId: string
}

function LateAnswerQuestion({
  question,
  loopApiId,
}: LateAnswerQuestionProps): JSX.Element {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const showToast = useCustomToast()
  const [responseText, setResponseText] = useState("")
  const textareaRef = useAutoResizeTextarea(responseText)

  const mutation = useMutation({
    mutationFn: async ({
      text,
      questionApiId,
      participantApiId,
    }: {
      text: string
      questionApiId: string
      participantApiId: string
    }) => {
      await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
        path: { question_api_id: questionApiId },
        body: {
          response_text: text,
          participant_api_identifier: participantApiId,
        },
        throwOnError: true,
      })
    },
    onSuccess: () => {
      showToast("Success!", "Your late answer has been submitted.", "success")
      setResponseText("")
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      })
    },
    onError: (
      err: AxiosError<UpsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(
          err.response?.data?.detail,
          "Failed to submit late answer. Please try again.",
        ),
        "error",
      )
    },
  })

  if (!currentUser) {
    return <div>Loading...</div>
  }

  const hasResponded = question.responses.some(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier,
  )

  if (hasResponded) {
    return <></>
  }

  const isSaving = mutation.isPending

  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResponseText(e.target.value)
  }

  const handleSubmit = async () => {
    if (isSaving) return
    if (!responseText.trim()) {
      showToast("Error", "Please enter your answer before submitting.", "error")
      return
    }
    await mutation.mutateAsync({
      text: responseText,
      questionApiId: question.api_identifier,
      participantApiId: currentUser.api_identifier,
    })
  }

  return (
    <div className="my-5 rounded-lg border bg-muted/50 p-4 sm:p-5">
      <div className="space-y-1">
        {question.author != null && (
          <p className="text-xs text-muted-foreground">
            {question.author.name} asked:
          </p>
        )}
        <h3 className="font-display text-base font-medium leading-relaxed">
          {question.question_text}
        </h3>
      </div>

      <div className="mb-3 mt-4">
        <Textarea
          ref={textareaRef}
          value={responseText}
          onChange={handleResponseChange}
          placeholder="Add your late answer here..."
          className="min-h-[100px] overflow-hidden resize-none"
          disabled={isSaving}
        />
      </div>

      <Button
        onClick={handleSubmit}
        disabled={isSaving || !responseText.trim()}
      >
        {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isSaving ? "Submitting..." : "Submit Late Answer"}
      </Button>
    </div>
  )
}

export default LateAnswerQuestion
