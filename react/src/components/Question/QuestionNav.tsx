import { Button } from "@/components/ui/button"
import { Plus, Sparkles } from "lucide-react"
import { useState } from "react"

import type { GroupLinked, PublicLetter } from "../../client"
import AddQuestion from "./AddQuestion"
import GenerateQuestion from "./GenerateQuestion"

type QuestionNavProps = {
  loop: PublicLetter
  group: GroupLinked
}

function QuestionNav(props: QuestionNavProps): JSX.Element {
  const [addQuestionOpen, setAddQuestionOpen] = useState(false)
  const [generateQuestionOpen, setGenerateQuestionOpen] = useState(false)

  const onClickAddQuestion = (): void => {
    setAddQuestionOpen(true)
  }

  const onClickGenerateQuestion = (): void => {
    setGenerateQuestionOpen(true)
  }
  return (
    <>
      <div className="flex flex-wrap gap-3">
        {props.loop.status === "UPCOMING" && (
          <Button onClick={() => onClickAddQuestion()}>
            <Plus className="h-4 w-4" /> Add new question
          </Button>
        )}
        {props.loop.status === "UPCOMING" && (
          <Button
            variant="outline"
            className="h-auto whitespace-normal py-2 text-left"
            onClick={() => onClickGenerateQuestion()}
          >
            <Sparkles className="h-4 w-4 text-muted-foreground" /> Ask ChatGPT
            to generate a question.
          </Button>
        )}

        <AddQuestion
          isOpen={addQuestionOpen}
          onClose={() => setAddQuestionOpen(false)}
          loopApiId={props.loop.api_identifier}
        />
        <GenerateQuestion
          isOpen={generateQuestionOpen}
          onClose={() => setGenerateQuestionOpen(false)}
          loopApiId={props.loop.api_identifier}
        />
      </div>
    </>
  )
}

export default QuestionNav
