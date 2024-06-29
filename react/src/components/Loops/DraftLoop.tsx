import { Container } from "@chakra-ui/react";
import { PublicLetter } from "../../client";
import DraftQuestion from "../Question/DraftQuestion";

function DraftLoop({ loop }: { loop: PublicLetter }) {
  return (
    <Container>
      {loop.questions.map((question) => {
        return (
          <DraftQuestion question={question} key={question.api_identifier} />
        );
      })}
    </Container>
  );
}

export default DraftLoop;
