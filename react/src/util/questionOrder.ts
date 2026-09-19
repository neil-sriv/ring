type QuestionOrderFields = {
  position?: number | null
  created_at: string
}

export function compareQuestionsByDisplayOrder(
  a: QuestionOrderFields,
  b: QuestionOrderFields,
): number {
  if (typeof a.position === "number" && typeof b.position === "number") {
    return a.position - b.position
  }
  return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
}
