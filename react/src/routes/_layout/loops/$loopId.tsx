import { Box, Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { LettersService, PublicLetter } from "../../../client";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import PublishedLoop from "../../../components/Loops/PublishedLoop";
import DraftLoop from "../../../components/Loops/DraftLoop";
import QuestionNav from "../../../components/Question/QuestionNav";
import { useSuspenseQuery } from "@tanstack/react-query";

type IssueLoaderProps = {
  loop: PublicLetter;
};

export const Route = createFileRoute("/_layout/loops/$loopId")({
  loader: async ({ params, context }): Promise<IssueLoaderProps> => {
    const loop = await context.queryClient.ensureQueryData({
      queryKey: ["loop", params.loopId],
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
  // const loop = Route.useLoaderData().loop;
  const routeParams = Route.useParams();
  const { data: loop } = useSuspenseQuery({
    queryKey: ["loop", routeParams.loopId],
    queryFn: async () => {
      return await LettersService.readLetterLettersLetterLetterApiIdGet({
        letterApiId: routeParams.loopId,
      });
    },
  });

  return (
    <Container maxW="container.lg" py={4}>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {loop.group.name} Issue #{loop.number}
      </Heading>
      {loop.status === "SENT" ? (
        <PublishedLoop loop={loop} />
      ) : (
        <>
          <QuestionNav loop={loop} />
          <DraftLoop loop={loop} />
        </>
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
