import type { PublicLetter } from "../../client"
import { questionsInDisplayOrder } from "../../util/questionOrder"
import DraftQuestion from "../Question/DraftQuestion"
import { ReorderQuestionButtons } from "../Question/ReorderQuestionButtons"
import { useReorderLetterQuestions } from "./useReorderLetterQuestions"

function DraftLoop({
  loop,
  canManage,
}: { loop: PublicLetter; canManage: boolean }) {
  const questions = questionsInDisplayOrder(loop.questions)
  const canReorder = canManage && loop.status !== "SENT" && questions.length > 1
  const reorder = useReorderLetterQuestions(loop.api_identifier)
  const orderedIds = questions.map((question) => question.api_identifier)

  return (
    <div className="w-full">
      {questions.map((question, index) => (
        <div
          key={question.api_identifier}
          className="flex items-start gap-2 border-b py-6 first:pt-0 last:border-b-0"
        >
          {canReorder && (
            <ReorderQuestionButtons
              questionText={question.question_text}
              canMoveUp={index > 0}
              canMoveDown={index < questions.length - 1}
              pending={reorder.pending}
              onMoveUp={() => reorder.move(orderedIds, index, -1)}
              onMoveDown={() => reorder.move(orderedIds, index, 1)}
            />
          )}
          <div className="min-w-0 flex-1">
            <DraftQuestion
              question={question}
              readOnly={loop.status === "UPCOMING"}
              loopApiId={loop.api_identifier}
              canManage={canManage}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

export default DraftLoop
