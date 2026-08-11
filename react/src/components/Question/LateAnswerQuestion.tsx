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
  const [isSubmitting, setIsSubmitting] = useState(false)
  const textareaRef = useAutoResizeTextarea(responseText)

  if (!currentUser) {
    return <div>Loading...</div>
  }

  // Check if user has already responded to this question
  const hasResponded = question.responses.some(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier,
  )

  // If user has already responded, don't show the late answer form
  if (hasResponded) {
    return <></>
  }

  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResponseText(e.target.value)
  }

  const mutation = useMutation({
    mutationFn: async () => {
      await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
        path: { question_api_id: question.api_identifier },
        body: {
          response_text: responseText,
          participant_api_identifier: currentUser.api_identifier,
        },
        throwOnError: true,
      })
    },
    onSuccess: () => {
      showToast("Success!", "Your late answer has been submitted.", "success")
      setResponseText("")
      // Invalidate the letter query to refresh the data
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
    onSettled: () => {
      setIsSubmitting(false)
    },
  })

  const handleSubmit = async () => {
    if (!responseText.trim()) {
      showToast("Error", "Please enter your answer before submitting.", "error")
      return
    }
    setIsSubmitting(true)
    mutation.mutate()
  }

  return (
    <div className="my-5 p-4 border border-gray-200 rounded-md bg-gray-50 dark:border-gray-600 dark:bg-gray-700">
      <h3 className="text-lg font-semibold mb-3 text-foreground">
        {question.author == null ? (
          question.question_text
        ) : (
          <>
            {question.author.name} asked: {question.question_text}
          </>
        )}
      </h3>

      <div className="mb-3">
        <Textarea
          ref={textareaRef}
          value={responseText}
          onChange={handleResponseChange}
          placeholder="Add your late answer here..."
          className="min-h-[100px] overflow-hidden resize-none bg-muted"
        />
      </div>

      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !responseText.trim()}
      >
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isSubmitting ? "Submitting..." : "Submit Late Answer"}
      </Button>
    </div>
  )
}

export default LateAnswerQuestion
