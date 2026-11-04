import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronUp } from "lucide-react"

interface ReorderQuestionButtonsProps {
  questionText: string
  canMoveUp: boolean
  canMoveDown: boolean
  pending: boolean
  onMoveUp: () => void
  onMoveDown: () => void
}

export function ReorderQuestionButtons({
  questionText,
  canMoveUp,
  canMoveDown,
  pending,
  onMoveUp,
  onMoveDown,
}: ReorderQuestionButtonsProps) {
  return (
    <div className="flex shrink-0 flex-col gap-1 text-muted-foreground">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label={`Move up: ${questionText}`}
        disabled={!canMoveUp || pending}
        onClick={onMoveUp}
      >
        <ChevronUp className="h-4 w-4" aria-hidden="true" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label={`Move down: ${questionText}`}
        disabled={!canMoveDown || pending}
        onClick={onMoveDown}
      >
        <ChevronDown className="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  )
}
