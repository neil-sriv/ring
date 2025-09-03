import { Badge, Box, Heading, Link, Text, useColorModeValue } from "@chakra-ui/react";
import { PublicQuestion, ResponseWithParticipant } from "../../client";
import { splitText, URLMatch } from "../../util/URLParse";
import { S3Image, S3Video } from "../Common/SingleUploadImage";

function TextBlockWithUrls({
  texts,
  responseApiId,
}: {
  texts: string[];
  responseApiId: string;
}): JSX.Element {
  const elements = new Array<JSX.Element>();
  texts.forEach((text, index) => {
    if (URLMatch(text) != null) {
      elements.push(
        <Link key={"" + index + responseApiId} href={text} isExternal={true}>
          {text}
        </Link>
      );
    } else {
      elements.push(
        <Text whiteSpace="pre-line" key={"" + index + responseApiId}>
          {text}
        </Text>
      );
    }
  });
  return <>{elements}</>;
}

function ResponseBlock({ response, isLateAnswer }: { response: ResponseWithParticipant; isLateAnswer?: boolean }) {
  let responseText = [response.response_text];
  const urlMatches = URLMatch(response.response_text);
  if (urlMatches != null) {
    responseText = splitText(response.response_text);
  }

  const bgColor = useColorModeValue(
    isLateAnswer ? "purple.50" : "transparent",
    isLateAnswer ? "purple.900" : "transparent"
  );
  const borderColor = useColorModeValue(
    isLateAnswer ? "purple.200" : "transparent",
    isLateAnswer ? "purple.600" : "transparent"
  );

  return (
    <Box
      my="10px"
      p={isLateAnswer ? "3" : "0"}
      bg={bgColor}
      border={isLateAnswer ? "1px" : "none"}
      borderColor={borderColor}
      borderRadius={isLateAnswer ? "md" : "0"}
    >
      <Box display="flex" alignItems="center" gap="2" mb="2">
        <Heading size="md">{response.participant.name}</Heading>
        {isLateAnswer && (
          <Badge colorScheme="purple" variant="subtle" fontSize="xs">
            Late Answer
          </Badge>
        )}
      </Box>
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
        );
      })}
    </Box>
  );
}

function PublishedQuestion({
  question,
  letterSendAt,
}: {
  question: PublicQuestion;
  letterSendAt?: string;
}): JSX.Element {
  // Determine which responses are late answers
  // A response is considered "late" if it was submitted after the letter was scheduled to be sent
  const letterSendDate = letterSendAt ? new Date(letterSendAt) : null;

  return (
    <Box my="20px">
      {question.author == null ? (
        <Heading size="lg">{question.question_text}</Heading>
      ) : (
        <Heading size="lg">
          {question.author.name} asked: {question.question_text}
        </Heading>
      )}
      {question.responses.map((response) => {
        const responseCreatedAt = new Date(response.created_at);
        const isLateAnswer = letterSendDate ? responseCreatedAt > letterSendDate : false;

        return (
          <ResponseBlock
            response={response}
            key={response.api_identifier}
            isLateAnswer={isLateAnswer}
          />
        );
      })}
    </Box>
  );
}

export default PublishedQuestion;
