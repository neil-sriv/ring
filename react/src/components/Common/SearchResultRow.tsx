import { Badge } from "@/components/ui/badge"
import { TableCell, TableRow } from "@/components/ui/table"
import { Link } from "@tanstack/react-router"
import type {
  SearchGroupSnippet,
  SearchLetterSnippet,
  SearchQuestionSnippet,
  SearchResponseSnippet,
  SearchResult,
  SearchUserSnippet,
} from "../../client"

interface SearchResultRowProps {
  result: SearchResult
}

function ResponseSearchResultRow({
  model,
}: {
  model: SearchResponseSnippet
}) {
  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <Link
          to="/loops/$loopId"
          params={{ loopId: model.letter_api_identifier }}
          style={{ textDecoration: "none" }}
        >
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              <Badge className="bg-blue-500 text-white hover:bg-blue-600">
                Response
              </Badge>
              <span className="font-medium">
                {model.group_name} - Letter {model.letter_number}
              </span>
            </div>
            <div className="flex gap-2 items-center">
              <span className="font-medium">Q: {model.question_text}</span>
            </div>
            <div className="flex gap-2 items-center">
              <span className="font-medium">by {model.participant_name}</span>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {model.response_text}
            </p>
          </div>
        </Link>
      </TableCell>
    </TableRow>
  )
}

function UserSearchResultRow({ model }: { model: SearchUserSnippet }) {
  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <div className="flex flex-col gap-2">
          <div className="flex gap-2 items-center">
            <Badge className="bg-green-500 text-white hover:bg-green-600">
              User
            </Badge>
            <span className="font-medium">{model.name}</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Member of {model.group_count} groups
          </p>
        </div>
      </TableCell>
    </TableRow>
  )
}

function GroupSearchResultRow({ model }: { model: SearchGroupSnippet }) {
  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <Link
          to="/groups/$groupId/loops"
          params={{ groupId: model.api_identifier }}
          style={{ textDecoration: "none" }}
        >
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              <Badge className="bg-purple-500 text-white hover:bg-purple-600">
                Group
              </Badge>
              <span className="font-medium">{model.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              {model.member_count} members • {model.letter_count} letters
            </p>
          </div>
        </Link>
      </TableCell>
    </TableRow>
  )
}

function QuestionSearchResultRow({
  model,
}: {
  model: SearchQuestionSnippet
}) {
  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <Link
          to="/loops/$loopId"
          params={{ loopId: model.letter_api_identifier }}
          style={{ textDecoration: "none" }}
        >
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              <Badge className="bg-orange-500 text-white hover:bg-orange-600">
                Question
              </Badge>
              <span className="font-medium">
                {model.group_name} - Letter {model.letter_number}
              </span>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {model.question_text}
            </p>
            <p className="text-sm text-muted-foreground/70">
              {model.response_count} responses
            </p>
          </div>
        </Link>
      </TableCell>
    </TableRow>
  )
}

function LetterSearchResultRow({ model }: { model: SearchLetterSnippet }) {
  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <Link
          to="/loops/$loopId"
          params={{ loopId: model.api_identifier }}
          style={{ textDecoration: "none" }}
        >
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              <Badge className="bg-teal-500 text-white hover:bg-teal-600">
                Letter
              </Badge>
              <span className="font-medium">
                {model.group_name} - Letter {model.number}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {model.participant_count} participants • {model.question_count}{" "}
              questions
            </p>
          </div>
        </Link>
      </TableCell>
    </TableRow>
  )
}

function DefaultSearchResultRow({ result }: { result: SearchResult }) {
  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <div className="flex flex-col gap-1">
          <span className="font-medium">{result.type}</span>
          <Badge className="w-fit bg-blue-500 text-white hover:bg-blue-600">
            Search result
          </Badge>
        </div>
      </TableCell>
    </TableRow>
  )
}

export function SearchResultRow({ result }: SearchResultRowProps) {
  switch (result.type) {
    case "SearchResponseSnippet":
      return (
        <ResponseSearchResultRow
          model={result.model as SearchResponseSnippet}
        />
      )
    case "SearchUserSnippet":
      return <UserSearchResultRow model={result.model as SearchUserSnippet} />
    case "SearchGroupSnippet":
      return <GroupSearchResultRow model={result.model as SearchGroupSnippet} />
    case "SearchQuestionSnippet":
      return (
        <QuestionSearchResultRow
          model={result.model as SearchQuestionSnippet}
        />
      )
    case "SearchLetterSnippet":
      return <LetterSearchResultRow model={result.model as SearchLetterSnippet} />
    default:
      return <DefaultSearchResultRow result={result} />
  }
}
