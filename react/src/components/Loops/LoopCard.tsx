import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { MinimalLetter, PublicLetter, UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import { formatResponderProgress } from "../../util/loopResponderProgress"

export function LoopCard(props: {
  loop: MinimalLetter | PublicLetter
  includeGroupName?: boolean
  showLoopTypeLabel?: boolean
  showResponderCount?: boolean
}): JSX.Element {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )

  const sendDate = new Date(props.loop.send_at)

  const getHeadingText = () => {
    if (props.loop.title) {
      return props.loop.title
    }
    if (props.loop.number) {
      return `Issue #${props.loop.number}`
    }
    return "Untitled Loop"
  }

  const getLoopTypeLabel = () => {
    if (!props.showLoopTypeLabel) return null

    const loopType = props.loop.letter_type
    if (loopType === "ADHOC") {
      return <Badge variant="secondary">One-off</Badge>
    }
    if (loopType === "CYCLIC") {
      return <Badge variant="outline">Recurring</Badge>
    }
    return null
  }

  const responderCount = props.showResponderCount
    ? formatResponderProgress(props.loop)
    : null

  const getUnansweredQuestionsCount = () => {
    if (
      props.loop.status === "SENT" &&
      currentUser &&
      "questions" in props.loop &&
      props.loop.questions
    ) {
      const unansweredQuestions = props.loop.questions.filter((question) => {
        return !question.responses.some(
          (response) =>
            response.participant.api_identifier === currentUser.api_identifier,
        )
      })
      return unansweredQuestions.length
    }
    return 0
  }

  const unansweredCount = getUnansweredQuestionsCount()

  return (
    <Link
      to="/loops/$loopId"
      params={{ loopId: props.loop.api_identifier }}
      className="block h-full no-underline"
    >
      <Card className="flex h-full flex-col gap-2 p-5 transition-shadow hover:shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <h3 className="min-w-0 font-display text-lg font-medium">
            {getHeadingText()}
          </h3>
          {getLoopTypeLabel()}
        </div>
        <p className="text-xs text-muted-foreground">
          {props.includeGroupName && <>{props.loop.group.name} &middot; </>}
          {sendDate.toLocaleDateString()}
        </p>
        {responderCount !== null && (
          <p className="text-xs text-muted-foreground">{responderCount}</p>
        )}
        {unansweredCount > 0 && (
          <Badge variant="warning" className="mt-auto">
            {unansweredCount} unanswered question
            {unansweredCount !== 1 ? "s" : ""}
          </Badge>
        )}
      </Card>
    </Link>
  )
}
