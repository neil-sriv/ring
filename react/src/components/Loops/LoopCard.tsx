import { Badge } from "@/components/ui/badge"
import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { MinimalLetter, PublicLetter, UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"

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
      return (
        <Badge
          variant="secondary"
          className="absolute top-2 right-2 bg-purple-100 text-purple-800 text-xs dark:bg-purple-900 dark:text-purple-200"
        >
          One-off
        </Badge>
      )
    }
    if (loopType === "CYCLIC") {
      return (
        <Badge
          variant="secondary"
          className="absolute top-2 right-2 bg-blue-100 text-blue-800 text-xs dark:bg-blue-900 dark:text-blue-200"
        >
          Recurring
        </Badge>
      )
    }
    return null
  }

  const getResponderCount = () => {
    if (
      props.showResponderCount &&
      "responders" in props.loop &&
      props.loop.responders
    ) {
      return props.loop.responders.length
    }
    return null
  }

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

  const responderCount = getResponderCount()
  const unansweredCount = getUnansweredQuestionsCount()

  return (
    <div className="h-full">
      <Link
        to="/loops/$loopId"
        params={{ loopId: props.loop.api_identifier }}
        className="block h-full no-underline"
      >
        <div className="relative h-full rounded-xl border border-border/50 bg-background/80 p-6 shadow-md backdrop-blur-sm transition-all duration-200 hover:-translate-y-1 hover:border-primary hover:shadow-xl dark:border-border/30 dark:bg-background/60">
          {getLoopTypeLabel()}
          <div className="flex flex-col items-start gap-2">
            <h3 className="text-lg font-semibold text-foreground">
              {getHeadingText()}
            </h3>
            {props.includeGroupName && (
              <p className="text-sm text-muted-foreground">
                {props.loop.group.name}
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              {sendDate.toLocaleDateString()}
            </p>
            {responderCount !== null && (
              <p className="text-sm text-muted-foreground">
                {responderCount} responder{responderCount !== 1 ? "s" : ""}
              </p>
            )}
            {unansweredCount > 0 && (
              <p className="text-sm font-medium text-orange-500">
                You have {unansweredCount} unanswered question
                {unansweredCount !== 1 ? "s" : ""}
              </p>
            )}
          </div>
        </div>
      </Link>
    </div>
  )
}
