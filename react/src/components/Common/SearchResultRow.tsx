import { Badge } from "@/components/ui/badge"
import { TableCell, TableRow } from "@/components/ui/table"
import { Link } from "@tanstack/react-router"
import type {
  GroupLinked,
  LetterUnlinked,
  PublicLetter,
  QuestionLinked,
  ResponseLinked,
  SearchResult,
  UserLinked,
} from "../../client"

interface SearchResultRowProps {
  result: SearchResult
}

function ResponseSearchResultRow({ result }: { result: SearchResult }) {
  const model = result.model as ResponseLinked

  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <Link
          to="/loops/$loopId"
          params={{ loopId: model.letter?.api_identifier ?? "" }}
          style={{ textDecoration: "none" }}
        >
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              <Badge className="bg-blue-500 text-white hover:bg-blue-600">
                Response
              </Badge>
              <span className="font-medium">
                {model.group?.name} - Letter {model.letter?.number}
              </span>
            </div>
            <div className="flex gap-2 items-center">
              <span className="font-medium">
                Q: {model.question.question_text}
              </span>
            </div>
            <div className="flex gap-2 items-center">
              <span className="font-medium">by {model.participant.name}</span>
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

function UserSearchResultRow({ result }: { result: SearchResult }) {
  const model = result.model as UserLinked

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
            Member of {model.groups.length} groups
          </p>
        </div>
      </TableCell>
    </TableRow>
  )
}

function GroupSearchResultRow({ result }: { result: SearchResult }) {
  const model = result.model as GroupLinked

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
              {model.members.length} members • {model.letter_count ?? 0} letters
            </p>
          </div>
        </Link>
      </TableCell>
    </TableRow>
  )
}

function QuestionSearchResultRow({ result }: { result: SearchResult }) {
  const model = result.model as QuestionLinked
  const letter = model.letter as LetterUnlinked

  return (
    <TableRow className="cursor-pointer">
      <TableCell>
        <Link
          to="/loops/$loopId"
          params={{ loopId: letter.api_identifier }}
          style={{ textDecoration: "none" }}
        >
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 items-center">
              <Badge className="bg-orange-500 text-white hover:bg-orange-600">
                Question
              </Badge>
              <span className="font-medium">
                {model.group.name} - Letter {letter.number}
              </span>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {model.question_text}
            </p>
            <p className="text-sm text-muted-foreground/70">
              {model.responses.length} responses
            </p>
          </div>
        </Link>
      </TableCell>
    </TableRow>
  )
}

function LetterSearchResultRow({ result }: { result: SearchResult }) {
  const model = result.model as PublicLetter

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
                {model.group.name} - Letter {model.number}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {model.participants.length} participants •{" "}
              {model.questions.length} questions
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
          <span className="font-medium">{result.model.api_identifier}</span>
          <Badge className="w-fit bg-blue-500 text-white hover:bg-blue-600">
            {result.type.replace("Linked", "")}
          </Badge>
        </div>
      </TableCell>
    </TableRow>
  )
}

export function SearchResultRow({ result }: SearchResultRowProps) {
  switch (result.type) {
    case "ResponseLinked":
      return <ResponseSearchResultRow result={result} />
    case "UserLinked":
      return <UserSearchResultRow result={result} />
    case "GroupLinked":
      return <GroupSearchResultRow result={result} />
    case "QuestionLinked":
      return <QuestionSearchResultRow result={result} />
    case "PublicLetter":
      return <LetterSearchResultRow result={result} />
    default:
      return <DefaultSearchResultRow result={result} />
  }
}
