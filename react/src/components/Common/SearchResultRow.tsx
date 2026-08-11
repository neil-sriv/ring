import { Badge } from "@/components/ui/badge"
import { TableCell, TableRow } from "@/components/ui/table"
import { Link } from "@tanstack/react-router"
import type { SearchHit } from "../../client"

interface SearchResultRowProps {
  result: SearchHit
}

const badgeClassByType: Record<SearchHit["type"], string> = {
  user: "bg-green-500 text-white hover:bg-green-600",
  group: "bg-purple-500 text-white hover:bg-purple-600",
  letter: "bg-teal-500 text-white hover:bg-teal-600",
  question: "bg-orange-500 text-white hover:bg-orange-600",
  response: "bg-blue-500 text-white hover:bg-blue-600",
}

const labelByType: Record<SearchHit["type"], string> = {
  user: "User",
  group: "Group",
  letter: "Letter",
  question: "Question",
  response: "Response",
}

function SearchResultContent({ result }: SearchResultRowProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2 items-center">
        <Badge className={badgeClassByType[result.type]}>
          {labelByType[result.type]}
        </Badge>
        <span className="font-medium">{result.title}</span>
      </div>
      {result.type === "response" && result.detail && (
        <p className="text-sm font-medium line-clamp-2">{result.detail}</p>
      )}
      {result.subtitle && (
        <p className="text-sm text-muted-foreground line-clamp-2">
          {result.subtitle}
        </p>
      )}
      {result.type !== "response" && result.detail && (
        <p className="text-sm text-muted-foreground/70">{result.detail}</p>
      )}
    </div>
  )
}

export function SearchResultRow({ result }: SearchResultRowProps) {
  const content = <SearchResultContent result={result} />

  if (result.href_loop_id) {
    return (
      <TableRow className="cursor-pointer">
        <TableCell>
          <Link
            to="/loops/$loopId"
            params={{ loopId: result.href_loop_id }}
            style={{ textDecoration: "none" }}
          >
            {content}
          </Link>
        </TableCell>
      </TableRow>
    )
  }

  if (result.href_group_id) {
    return (
      <TableRow className="cursor-pointer">
        <TableCell>
          <Link
            to="/groups/$groupId/loops"
            params={{ groupId: result.href_group_id }}
            style={{ textDecoration: "none" }}
          >
            {content}
          </Link>
        </TableCell>
      </TableRow>
    )
  }

  return (
    <TableRow>
      <TableCell>{content}</TableCell>
    </TableRow>
  )
}
