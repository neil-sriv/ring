import { Button } from "@/components/ui/button"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import type { PublicLetter, UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import LateAnswerQuestion from "../Question/LateAnswerQuestion"
import PublishedQuestion from "../Question/PublishedQuestion"

function PublishedLoop({ loop }: { loop: PublicLetter }) {
  const [showLateAnswers, setShowLateAnswers] = useState(false)
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )

  if (!currentUser) {
    return (
      <div className="w-full text-sm text-muted-foreground">Loading...</div>
    )
  }

  // Get questions the user hasn't answered
  const unansweredQuestions = loop.questions.filter((question) => {
    return !question.responses.some(
      (response) =>
        response.participant.api_identifier === currentUser.api_identifier,
    )
  })

  const hasUnansweredQuestions = unansweredQuestions.length > 0

  return (
    <div className="w-full">
      {/* Late Answers Toggle */}
      {hasUnansweredQuestions && (
        <div className="mb-6 rounded-lg border border-info/25 bg-info/10 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">Late Answers Available</p>
              <p className="text-sm text-muted-foreground">
                You have {unansweredQuestions.length} question
                {unansweredQuestions.length !== 1 ? "s" : ""} you haven't
                answered yet.
              </p>
            </div>
            <Button
              variant={showLateAnswers ? "default" : "outline"}
              onClick={() => setShowLateAnswers(!showLateAnswers)}
            >
              {showLateAnswers ? "Hide Late Answers" : "Show Late Answers"}
            </Button>
          </div>
        </div>
      )}

      {/* Late Answer Questions */}
      {showLateAnswers && hasUnansweredQuestions && (
        <div className="mb-6">
          <p className="mb-4 text-base font-semibold">
            Questions You Haven't Answered
          </p>
          {unansweredQuestions.map((question) => (
            <LateAnswerQuestion
              key={question.api_identifier}
              question={question}
              loopApiId={loop.api_identifier}
            />
          ))}
        </div>
      )}

      {/* All Questions (Published) */}
      <div>
        <p className="mb-4 text-base font-semibold">
          All Questions and Responses
        </p>
        {loop.questions
          .sort(
            (a, b) =>
              new Date(b.created_at).getTime() -
              new Date(a.created_at).getTime(),
          )
          .map((question) => {
            return (
              <PublishedQuestion
                question={question}
                key={question.api_identifier}
                letterSendAt={loop.send_at}
              />
            )
          })}
      </div>
    </div>
  )
}

export default PublishedLoop
