import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { PublicQuestion, ResponseWithParticipant } from "../../client"
import { URLMatch, splitText } from "../../util/URLParse"
import { S3Image, S3Video } from "../Common/SingleUploadImage"

function TextBlockWithUrls({
  texts,
  responseApiId,
}: {
  texts: string[]
  responseApiId: string
}): JSX.Element {
  const elements = new Array<JSX.Element>()
  texts.forEach((text, index) => {
    if (URLMatch(text) != null) {
      elements.push(
        <a
          key={`${index}${responseApiId}`}
          href={text}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline hover:opacity-80"
        >
          {text}
        </a>,
      )
    } else {
      elements.push(
        <p className="whitespace-pre-line" key={`${index}${responseApiId}`}>
          {text}
        </p>,
      )
    }
  })
  return <>{elements}</>
}

function ResponseBlock({
  response,
  isLateAnswer,
}: { response: ResponseWithParticipant; isLateAnswer?: boolean }) {
  let responseText = [response.response_text]
  const urlMatches = URLMatch(response.response_text)
  if (urlMatches != null) {
    responseText = splitText(response.response_text)
  }

  return (
    <div
      className={cn(
        "my-2.5",
        isLateAnswer
          ? "p-3 bg-purple-50 border border-purple-200 rounded-md dark:bg-purple-900 dark:border-purple-600"
          : "",
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-lg font-semibold">{response.participant.name}</h3>
        {isLateAnswer && (
          <Badge
            variant="secondary"
            className="text-xs bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200"
          >
            Late Answer
          </Badge>
        )}
      </div>
      {/* <Text>{responseText}</Text> */}
      <TextBlockWithUrls
        texts={responseText}
        responseApiId={response.api_identifier}
      />
      {response.images.map((image) => {
        return image.media_type === "image" ? (
          <S3Image
            s3Key={image.s3_url}
            alt={`Photo from ${response.participant.name}`}
            key={image.s3_url}
            expandable
          />
        ) : (
          <S3Video s3Key={image.s3_url} key={image.s3_url} />
        )
      })}
    </div>
  )
}

function PublishedQuestion({
  question,
  letterSendAt,
}: {
  question: PublicQuestion
  letterSendAt?: string
}): JSX.Element {
  // Determine which responses are late answers
  // A response is considered "late" if it was submitted after the letter was scheduled to be sent
  const letterSendDate = letterSendAt ? new Date(letterSendAt) : null

  return (
    <div className="my-5">
      {question.author == null ? (
        <h2 className="text-2xl font-bold">{question.question_text}</h2>
      ) : (
        <h2 className="text-2xl font-bold">
          {question.author.name} asked: {question.question_text}
        </h2>
      )}
      {question.responses.map((response) => {
        const responseCreatedAt = new Date(response.created_at)
        const isLateAnswer = letterSendDate
          ? responseCreatedAt > letterSendDate
          : false

        return (
          <ResponseBlock
            response={response}
            key={response.api_identifier}
            isLateAnswer={isLateAnswer}
          />
        )
      })}
    </div>
  )
}

export default PublishedQuestion
