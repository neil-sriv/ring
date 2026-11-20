import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { useState } from "react"
import type { PublicLetter } from "../../client"
import { isLateQuestionCutoffReached } from "../../util/lateQuestion"
import AddLateQuestion, {
  LateQuestionBanner,
} from "../Question/AddLateQuestion"
import AddQuestion from "../Question/AddQuestion"
import GenerateQuestion from "../Question/GenerateQuestion"

interface LoopQuestionActionsProps {
  loop: PublicLetter
}

/**
 * Upcoming loops keep the normal add buttons. In-progress loops get the
 * late-question banner and composer. Sent loops get neither.
 */
export function LoopQuestionActions({ loop }: LoopQuestionActionsProps) {
  const [addQuestionOpen, setAddQuestionOpen] = useState(false)
  const [generateQuestionOpen, setGenerateQuestionOpen] = useState(false)
  const [lateComposerOpen, setLateComposerOpen] = useState(false)
  const cutoffReached = isLateQuestionCutoffReached(loop)
  const showLateComposer =
    loop.status === "IN_PROGRESS" && (lateComposerOpen || cutoffReached)

  return (
    <>
      {loop.status === "UPCOMING" && (
        <div className="mt-6 flex flex-wrap gap-3">
          <Button type="button" onClick={() => setAddQuestionOpen(true)}>
            <Plus className="h-4 w-4" /> Add new question
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => setGenerateQuestionOpen(true)}
          >
            <Plus className="h-4 w-4" /> Ask ChatGPT to generate a question.
          </Button>
        </div>
      )}

      {loop.status === "IN_PROGRESS" && (
        <div className="mt-6">
          <LateQuestionBanner
            cutoffReached={cutoffReached}
            composerOpen={lateComposerOpen && !cutoffReached}
            onToggle={() => setLateComposerOpen((open) => !open)}
          />
          {showLateComposer && (
            <AddLateQuestion
              loop={loop}
              disabled={cutoffReached}
              onAdded={() => setLateComposerOpen(false)}
            />
          )}
        </div>
      )}

      <AddQuestion
        isOpen={addQuestionOpen}
        onClose={() => setAddQuestionOpen(false)}
        loopApiId={loop.api_identifier}
      />
      <GenerateQuestion
        isOpen={generateQuestionOpen}
        onClose={() => setGenerateQuestionOpen(false)}
        loopApiId={loop.api_identifier}
      />
    </>
  )
}
