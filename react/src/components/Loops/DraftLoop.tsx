import type { PublicLetter } from "../../client"
import { compareQuestionsByDisplayOrder } from "../../util/questionOrder"
import DraftQuestion from "../Question/DraftQuestion"

function DraftLoop({
  loop,
  isGroupAdmin,
}: { loop: PublicLetter; isGroupAdmin: boolean }) {
  return (
    <div className="w-full">
      {[...loop.questions]
        .sort(compareQuestionsByDisplayOrder)
        .map((question) => {
          return (
            <DraftQuestion
              question={question}
              key={question.api_identifier}
              readOnly={loop.status === "UPCOMING"}
              loopApiId={loop.api_identifier}
              isGroupAdmin={isGroupAdmin}
            />
          )
        })}
    </div>
  )
}

export default DraftLoop
