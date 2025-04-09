import { Box, Container, Flex, Heading, Text, VStack } from "@chakra-ui/react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { PublicLetter, UserLinked } from "../../../client";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import PublishedLoop from "../../../components/Loops/PublishedLoop";
import DraftLoop from "../../../components/Loops/DraftLoop";
import QuestionNav from "../../../components/Question/QuestionNav";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import {
  readGroupPartiesGroupGroupApiIdGetOptions,
  readLetterLettersLetterLetterApiIdGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../../client/@tanstack/react-query.gen";

type IssueLoaderProps = {
  loop: PublicLetter;
};

export const Route = createFileRoute("/_layout/loops/$loopId")({
  loader: async ({ params, context }): Promise<IssueLoaderProps> => {
    const loop = await context.queryClient.ensureQueryData({
      ...readLetterLettersLetterLetterApiIdGetOptions({
        path: { letter_api_id: params.loopId },
      }),
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
    ...readLetterLettersLetterLetterApiIdGetOptions({
      path: { letter_api_id: routeParams.loopId },
    }),
  });
  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: loop.group.api_identifier },
    }),
  });
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
  const localDueDate = new Date(loop.send_at);

  return (
    <Flex justify="center" w="100%">
      <Box maxW="1200px" w="100%" px={[2, 4]}>
        <VStack spacing={[4, 6, 8]} align="center" w="100%">
          <Box w="100%">
            <Heading size={["md", "lg"]} textAlign="center">
              <Link
                to="/groups/$groupId/loops"
                params={{ groupId: group!.api_identifier }}
                style={{ textDecoration: "underline" }}
              >
                {group!.name}
              </Link>
            </Heading>
            <Heading size={["md", "lg"]}>
              <p> Issue #{loop.number}</p>
            </Heading>
            {loop.status === "IN_PROGRESS" && (
              <Heading
                size="md"
                textAlign={{ base: "center", md: "left" }}
                pt={2}
              >
                Due {localDueDate.toLocaleString()}
              </Heading>
            )}
          </Box>

          <Box w="100%">
            <QuestionNav loop={loop} group={group} />
          </Box>

          {loop.status === "SENT" ? (
            <PublishedLoop loop={loop} />
          ) : (
            <DraftLoop loop={loop} isGroupAdmin={group.admin.api_identifier === currentUser?.api_identifier} />
          )}
        </VStack>
      </Box>
    </Flex>
  );
}

function Issue() {
  return (
    <Container maxW="full">
      <Box pt={[4, 8, 12]} mx={[2, 4]}>
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
    </Container>
  );
}
