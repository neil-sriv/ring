import { Badge } from "@/components/ui/badge"

/**
 * Marks a question added while its loop was in progress.
 * Uses warning, not the info variant that marks a "Late Answer".
 */
export function LateQuestionBadge(): JSX.Element {
  return <Badge variant="warning">Late</Badge>
}
