import { Container } from "@chakra-ui/react";
import PublishedQuestion from "../Question/PublishedQuestion";
import { PublicLetter } from "../../client";

function PublishedLoop({ loop }: { loop: PublicLetter }) {
  return (
    <Container>
      {loop.questions.map((question) => {
        return (
          <PublishedQuestion
            question={question}
            key={question.api_identifier}
          />
        );
      })}
    </Container>
  );
}

export default PublishedLoop;
