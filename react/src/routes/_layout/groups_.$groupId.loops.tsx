import { Container, Heading, Text } from "@chakra-ui/react";
// import Navbar from "../../components/Common/Navbar";
import { createFileRoute } from "@tanstack/react-router";
import { LettersService, PublicLetter } from "../../client";

export const Route = createFileRoute("/_layout/groups/$groupId/loops")({
  loaderDeps: ({ search: { offset, limit } }) => ({ offset, limit }),
  loader: async ({
    params,
    deps: { offset, limit },
  }): Promise<PublicLetter[]> => {
    const loops = await LettersService.listLettersLettersLettersGet({
      groupApiId: params.groupId,
      skip: offset,
      limit,
    });
    return loops;
  },
  component: Loops,
});

function Loops() {
  const props = Route.useLoaderData();
  console.log("props", props);
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {props[0].group.name}
      </Heading>
      <Text>Some text</Text>

      {/* <Navbar type={"Loop"} /> */}
    </Container>
  );
}
