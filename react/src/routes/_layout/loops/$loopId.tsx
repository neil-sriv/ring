import { Box, Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { LettersService, PublicLetter } from "../../../client";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import PublishedLoop from "../../../components/Loops/PublishedLoop";
import DraftLoop from "../../../components/Loops/DraftLoop";

type IssueLoaderProps = {
  loop: PublicLetter;
};

export const Route = createFileRoute("/_layout/loops/$loopId")({
  loader: async ({ params, context }): Promise<IssueLoaderProps> => {
    const loop = await context.queryClient.ensureQueryData({
      queryKey: ["loops", params.loopId],
      queryFn: async () => {
        return await LettersService.readLetterLettersLetterLetterApiIdGet({
          letterApiId: params.loopId,
        });
      },
    });

    return {
      loop,
    };
  },
  component: Issue,
});

function IssueContent() {
  const loop = Route.useLoaderData().loop;
  return (
    <Container maxW="container.lg" py={4}>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {loop.group.name} Issue #{loop.number}
      </Heading>
      {/* <Container maxW="container.lg" py={4}>
        <SimpleGrid columns={4} gap={4}>
          {props.loops.map((loop) => (
            <LoopCard key={loop.api_identifier} loop={loop} />
          ))}
        </SimpleGrid>
      </Container> */}
      {loop.status === "SENT" ? (
        <PublishedLoop loop={loop} />
      ) : (
        <DraftLoop loop={loop} />
      )}
    </Container>
  );
}

function Issue() {
  return (
    <Box>
      <ErrorBoundary
        fallbackRender={({ error }) => (
          <Box>
            <Heading>Error</Heading>
            <Text>{error.message}</Text>
          </Box>
        )}
      >
        <Suspense fallback={<Box>Loading...</Box>}>
          <IssueContent />
        </Suspense>
      </ErrorBoundary>
    </Box>
  );
}
