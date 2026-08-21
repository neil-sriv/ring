import { Link } from "@tanstack/react-router"
import {
  Mail,
  MessageCircleQuestion,
  MessageSquare,
  User,
  Users,
} from "lucide-react"
import type { SearchHit } from "../../client"

interface SearchResultRowProps {
  result: SearchHit
}

const iconByType: Record<SearchHit["type"], typeof Mail> = {
  user: User,
  group: Users,
  letter: Mail,
  question: MessageCircleQuestion,
  response: MessageSquare,
}

const labelByType: Record<SearchHit["type"], string> = {
  user: "User",
  group: "Group",
  letter: "Letter",
  question: "Question",
  response: "Response",
}

function SearchResultContent({ result }: SearchResultRowProps) {
  const Icon = iconByType[result.type]

  return (
    <div className="flex items-start gap-3">
      <Icon
        className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
        strokeWidth={1.5}
      />
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
          <span className="text-sm font-medium">{result.title}</span>
          <span className="text-xs text-muted-foreground">
            {labelByType[result.type]}
          </span>
        </div>
        {result.type === "response" && result.detail && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {result.detail}
          </p>
        )}
        {result.subtitle && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {result.subtitle}
          </p>
        )}
        {result.type !== "response" && result.detail && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {result.detail}
          </p>
        )}
      </div>
    </div>
  )
}

export function SearchResultRow({ result }: SearchResultRowProps) {
  const content = <SearchResultContent result={result} />

  if (result.href_loop_id) {
    return (
      <Link
        to="/loops/$loopId"
        params={{ loopId: result.href_loop_id }}
        className="block rounded-md px-3 py-2.5 no-underline transition-colors hover:bg-accent"
      >
        {content}
      </Link>
    )
  }

  if (result.href_group_id) {
    return (
      <Link
        to="/groups/$groupId/loops"
        params={{ groupId: result.href_group_id }}
        className="block rounded-md px-3 py-2.5 no-underline transition-colors hover:bg-accent"
      >
        {content}
      </Link>
    )
  }

  return <div className="rounded-md px-3 py-2.5">{content}</div>
}
