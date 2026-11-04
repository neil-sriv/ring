type QuestionOrderFields = {
  position?: number | null
  created_at: string
}

type IdentifiedQuestion = QuestionOrderFields & {
  api_identifier: string
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

export function questionsInDisplayOrder<T extends QuestionOrderFields>(
  questions: readonly T[],
): T[] {
  return [...questions].sort(compareQuestionsByDisplayOrder)
}

export function withQuestionPositions<T extends IdentifiedQuestion>(
  questions: readonly T[],
  orderedIds: readonly string[],
): T[] {
  const byId = new Map(
    questions.map((question) => [question.api_identifier, question]),
  )
  const next: T[] = []
  orderedIds.forEach((id, position) => {
    const question = byId.get(id)
    if (question) {
      next.push({ ...question, position })
    }
  })
  return next
}

export function movedQuestionIds(
  orderedIds: readonly string[],
  index: number,
  delta: -1 | 1,
): string[] | undefined {
  const target = index + delta
  if (target < 0 || target >= orderedIds.length) {
    return undefined
  }
  const next = [...orderedIds]
  const [moved] = next.splice(index, 1)
  next.splice(target, 0, moved)
  return next
}
