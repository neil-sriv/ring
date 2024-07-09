import { Box, Heading, Text, Image } from "@chakra-ui/react";
import { PublicQuestion, ResponseWithParticipant } from "../../client";

function ResponseBlock({ response }: { response: ResponseWithParticipant }) {
  return (
    <Box my="10px">
      <Heading size="md">{response.participant.name}</Heading>
      <Text>{response.response_text}</Text>
      {response.image_urls.map((url) => {
        return <Image src={"https://du32exnxihxuf.cloudfront.net/" + url} />;
      })}
    </Box>
  );
}

function PublishedQuestion({
  question,
}: {
  question: PublicQuestion;
}): JSX.Element {
  return (
    <Box my="20px">
      <Heading>{question.question_text}</Heading>
      {question.responses.map((response) => {
        return (
          <ResponseBlock response={response} key={response.api_identifier} />
        );
      })}
    </Box>
  );
}

export default PublishedQuestion;
