import { Container } from "@chakra-ui/react";
import { PublicLetter } from "../../client";
import DraftQuestion from "../Question/DraftQuestion";

function DraftLoop({ loop }: { loop: PublicLetter }) {
  return (
    <Container>
      {loop.questions
        .sort((a, b) => a.created_at - b.created_at)
        .map((question) => {
          return (
            <DraftQuestion question={question} key={question.api_identifier} />
          );
        })}
    </Container>
  );
}

export default DraftLoop;
