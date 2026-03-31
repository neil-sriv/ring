import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
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
      <div className="flex gap-4 flex-wrap">
        {props.loop.status === "UPCOMING" && (
          <Button
            className="gap-1 text-sm md:text-base whitespace-normal text-left h-auto py-2 hover:-translate-y-0.5 transition-all duration-200"
            onClick={() => onClickAddQuestion()}
          >
            <Plus className="h-4 w-4" /> Add new question
          </Button>
        )}
        {props.loop.status === "UPCOMING" && (
          <Button
            className="gap-1 text-sm md:text-base whitespace-normal text-left h-auto py-2 hover:-translate-y-0.5 transition-all duration-200"
            onClick={() => onClickGenerateQuestion()}
          >
            <Plus className="h-4 w-4" /> Ask ChatGPT to generate a question.
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
