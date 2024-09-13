import { Container } from "@chakra-ui/react";
import PublishedQuestion from "../Question/PublishedQuestion";
import { PublicLetter } from "../../client";

function PublishedLoop({ loop }: { loop: PublicLetter }) {
  return (
    <Container>
      {loop.questions
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        .map((question) => {
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
