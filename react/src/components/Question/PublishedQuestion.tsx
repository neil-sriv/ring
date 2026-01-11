import { Box, Heading, Link, Text, VStack } from "@chakra-ui/react"
import type { PublicQuestion, ResponseWithParticipant } from "../../client"
import { URLMatch, splitText } from "../../util/URLParse"
import CommentSection from "../Comments/CommentSection"
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
        <Link key={`${index}${responseApiId}`} href={text} isExternal={true}>
          {text}
        </Link>,
      )
    } else {
      elements.push(
        <Text whiteSpace="pre-line" key={`${index}${responseApiId}`}>
          {text}
        </Text>,
      )
    }
  })
  return <>{elements}</>
}

function ResponseBlock({ response }: { response: ResponseWithParticipant }) {
  let responseText = [response.response_text]
  const urlMatches = URLMatch(response.response_text)
  if (urlMatches != null) {
    responseText = splitText(response.response_text)
  }
  return (
    <Box my="10px">
      <Heading size="md">{response.participant.name}</Heading>
      {/* <Text>{responseText}</Text> */}
      <TextBlockWithUrls
        texts={responseText}
        responseApiId={response.api_identifier}
      />
      {response.images.map((image) => {
        return image.media_type === "image" ? (
          <S3Image s3Key={image.s3_url} alt="IMAGE HERE" key={image.s3_url} />
        ) : (
          <S3Video s3Key={image.s3_url} key={image.s3_url} />
        )
      })}
    </Box>
  )
}

function PublishedQuestion({
  question,
}: {
  question: PublicQuestion
}): JSX.Element {
  return (
    <VStack spacing={6} align="stretch" my="20px">
      <Box>
        {question.author == null ? (
          <Heading size="lg">{question.question_text}</Heading>
        ) : (
          <Heading size="lg">
            {question.author.name} asked: {question.question_text}
          </Heading>
        )}
        {question.responses.map((response) => {
          return (
            <ResponseBlock response={response} key={response.api_identifier} />
          )
        })}
      </Box>

      <CommentSection questionApiId={question.api_identifier} />
    </VStack>
  )
}

export default PublishedQuestion
