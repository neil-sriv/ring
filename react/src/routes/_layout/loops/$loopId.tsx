import { Box, Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import {
  PublicLetter,
  readGroupPartiesGroupGroupApiIdGet,
  readLetterLettersLetterLetterApiIdGet,
} from "../../../client";
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
    const { data: loop } = await context.queryClient.ensureQueryData({
      queryKey: ["loop", params.loopId],
      queryFn: async () => {
        return await readLetterLettersLetterLetterApiIdGet({
          path: { letter_api_id: params.loopId },
        });
      },
    });

    if (!loop) {
      throw new Error("Failed to load loop");
    }

    return {
      loop,
    };
  },
  component: Issue,
});

function IssueContent() {
  const routeParams = Route.useParams();
  const {
    data: { data: loop },
  } = useSuspenseQuery({
    queryKey: ["loop", routeParams.loopId],
    queryFn: async () => {
      return await readLetterLettersLetterLetterApiIdGet({
        path: { letter_api_id: routeParams.loopId },
      });
    },
  });
  if (!loop) {
    return null;
  }
  const {
    data: { data: group },
  } = useSuspenseQuery({
    queryKey: ["group", loop.group.api_identifier],
    queryFn: async () => {
      return await readGroupPartiesGroupGroupApiIdGet({
        path: { group_api_id: loop.group.api_identifier },
      });
    },
  });
  if (!group) {
    return null;
  }
  const localDueDate = new Date(loop.send_at);

  return (
    <Container maxW="container.lg" py={4}>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {loop.group.name} Issue #{loop.number}
      </Heading>
      {loop.status === "IN_PROGRESS" && (
        <Heading size="md" textAlign={{ base: "center", md: "left" }} pt={2}>
          Due: {localDueDate.toLocaleString()}
        </Heading>
      )}
      {loop.status === "SENT" ? (
        <PublishedLoop loop={loop} />
      ) : (
        <>
          <QuestionNav loop={loop} group={group} />
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
