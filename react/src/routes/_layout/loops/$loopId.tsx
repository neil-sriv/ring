import { Box, Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { LettersService, PartiesService, PublicLetter } from "../../../client";
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
  const routeParams = Route.useParams();
  const { data: loop } = useSuspenseQuery({
    queryKey: ["loop", routeParams.loopId],
    queryFn: async () => {
      return await LettersService.readLetterLettersLetterLetterApiIdGet({
        letterApiId: routeParams.loopId,
      });
    },
  });
  const { data: group } = useSuspenseQuery({
    queryKey: ["group", loop.group.api_identifier],
    queryFn: async () => {
      return await PartiesService.readGroupPartiesGroupGroupApiIdGet({
        groupApiId: loop.group.api_identifier,
      });
    },
  });
  const localDueDate = new Date(loop.send_at);

  return (
    <Container maxW="container.lg" py={4}>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        <Link
          to="/groups/$groupId/loops"
          params={{ groupId: group!.api_identifier }}
          style={{ textDecoration: "underline" }}
        >
          {group!.name}
        </Link>
        <p> Issue #{loop.number}</p>
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
