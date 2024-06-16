import {
  Box,
  Card,
  CardHeader,
  Container,
  Flex,
  Heading,
  Text,
} from "@chakra-ui/react";
// import Navbar from "../../components/Common/Navbar";
import { createFileRoute } from "@tanstack/react-router";
import { LettersService, PartiesService, PublicLetter } from "../../client";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";

type LoopsLoaderProps = {
  loops: PublicLetter[];
};

export const Route = createFileRoute("/_layout/groups/$groupId/loops")({
  loaderDeps: ({ search: { offset, limit } }) => ({ offset, limit }),
  loader: async ({
    params,
    deps: { offset, limit },
  }): Promise<LoopsLoaderProps> => {
    const loops = await LettersService.listLettersLettersLettersGet({
      groupApiId: params.groupId,
      skip: offset,
      limit,
    });

    return {
      loops,
    };
  },
  component: Loops,
});

type LoopCardProps = {
  loop: PublicLetter;
};

function LoopCard(props: LoopCardProps): JSX.Element {
  return (
    <Card bgColor="blue">
      <CardHeader>
        <Heading size="md">{props.loop.number}</Heading>
      </CardHeader>
    </Card>
  );
}

function Loops() {
  const props = Route.useLoaderData();
  const groupId = Route.useParams().groupId;
  const { data: group, status } = useSuspenseQuery({
    queryKey: ["groups", groupId],
    queryFn: () =>
      PartiesService.readGroupPartiesGroupGroupApiIdGet({
        groupApiId: groupId,
      }),
  });
  console.log("props", props);
  console.log("group", group);
  console.log("status", status);
  return (
    <ErrorBoundary
      fallbackRender={({ error }) => (
        <Box>
          <Heading>Error</Heading>
          <Text>{error.message}</Text>
        </Box>
      )}
    >
      <Suspense fallback={<Box>Loading...</Box>}>
        <Container maxW="full">
          <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
            {group!.name}
          </Heading>
          <Text>Some text</Text>

          {/* <Navbar type={"Loop"} /> */}
          <Flex>
            {props.loops.map((loop) => (
              <LoopCard key={loop.api_identifier} loop={loop} />
            ))}
          </Flex>
        </Container>
      </Suspense>
    </ErrorBoundary>
  );
}
