import { Container, Heading } from "@chakra-ui/react";
import Navbar from "../../components/Common/Navbar";
import { createFileRoute } from "@tanstack/react-router";
import { LettersService, LetterLinked } from "../../client";

export const Route = createFileRoute("/_layout/groups/$groupId/loops")({
  loaderDeps: ({ search: { offset, limit } }) => ({ offset, limit }),
  loader: async ({ params, deps: { offset, limit } }) => {
    const loops = await LettersService.listLettersLettersLettersGet({
      groupApiId: params.groupId,
      skip: offset,
      limit,
    });
    return Loops({ loops });
  },
});

interface LoopsProps {
  loops: LetterLinked[];
}

function Loops(props: LoopsProps) {
  console.log("props", props);
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Loops
      </Heading>

      <Navbar type={"Loop"} />
    </Container>
  );
}
