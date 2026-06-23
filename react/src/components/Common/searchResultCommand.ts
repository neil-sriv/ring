import {
  FileText,
  HelpCircle,
  Mail,
  MessageSquare,
  Users,
} from "lucide-react"
import type { ComponentType } from "react"

import type {
  GroupLinked,
  PublicLetter,
  QuestionLinked,
  ResponseLinked,
  SearchResult,
  UserLinked,
} from "../../client"

export interface SearchCommandItem {
  id: string
  label: string
  description?: string
  icon: ComponentType<{ className?: string }>
  badge: string
  action: (() => void) | null
}

export function searchResultToCommandItem(
  result: SearchResult,
  navigate: (options: {
    to: string
    params?: Record<string, string>
  }) => void,
): SearchCommandItem {
  switch (result.type) {
    case "ResponseLinked": {
      const model = result.model as ResponseLinked
      const loopId = model.letter?.api_identifier
      return {
        id: `search-${model.api_identifier}`,
        label: `${model.group?.name ?? "Group"} · Letter ${model.letter?.number ?? "?"}`,
        description: `Q: ${model.question.question_text} · ${model.participant.name}`,
        icon: MessageSquare,
        badge: "Response",
        action: loopId
          ? () => navigate({ to: "/loops/$loopId", params: { loopId } })
          : null,
      }
    }
    case "UserLinked": {
      const model = result.model as UserLinked
      return {
        id: `search-${model.api_identifier}`,
        label: model.name,
        description: `Member of ${model.groups?.length ?? 0} groups`,
        icon: Users,
        badge: "User",
        action: null,
      }
    }
    case "GroupLinked": {
      const model = result.model as GroupLinked
      return {
        id: `search-${model.api_identifier}`,
        label: model.name,
        description: `${model.members?.length ?? 0} members · ${model.letters?.length ?? 0} letters`,
        icon: Users,
        badge: "Group",
        action: () =>
          navigate({
            to: "/groups/$groupId/loops",
            params: { groupId: model.api_identifier },
          }),
      }
    }
    case "QuestionLinked": {
      const model = result.model as QuestionLinked
      const loopId = model.letter?.api_identifier
      return {
        id: `search-${model.api_identifier}`,
        label: `${model.group.name} · Letter ${model.letter?.number ?? "?"}`,
        description: model.question_text,
        icon: HelpCircle,
        badge: "Question",
        action: loopId
          ? () => navigate({ to: "/loops/$loopId", params: { loopId } })
          : null,
      }
    }
    case "PublicLetter": {
      const model = result.model as PublicLetter
      return {
        id: `search-${model.api_identifier}`,
        label: `${model.group.name} · Letter ${model.number ?? "?"}`,
        description: `${model.participants?.length ?? 0} participants · ${model.questions?.length ?? 0} questions`,
        icon: Mail,
        badge: "Letter",
        action: () =>
          navigate({
            to: "/loops/$loopId",
            params: { loopId: model.api_identifier },
          }),
      }
    }
    default:
      return {
        id: `search-${result.model.api_identifier}`,
        label: result.model.api_identifier,
        description: result.type.replace("Linked", ""),
        icon: FileText,
        badge: result.type.replace("Linked", ""),
        action: null,
      }
  }
}
