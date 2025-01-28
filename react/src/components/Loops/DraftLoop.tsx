import { Container } from "@chakra-ui/react";
import { PublicLetter } from "../../client";
import DraftQuestion from "../Question/DraftQuestion";

function DraftLoop({ loop }: { loop: PublicLetter }) {
  return (
    <Container>
      {loop.questions
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        .map((question) => {
          return (
            <DraftQuestion
              question={question}
              key={question.api_identifier}
              readOnly={loop.status === "UPCOMING"}
              loopApiId={loop.api_identifier}
            />
          );
        })}
    </Container>
  );
}

export default DraftLoop;
