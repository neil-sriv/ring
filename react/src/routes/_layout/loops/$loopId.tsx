import { Box, Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import {
  LettersService,
  PublicLetter,
  PublicQuestion,
  ResponseWithParticipant,
} from "../../../client";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";

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

function ResponseBlock({ response }: { response: ResponseWithParticipant }) {
  return (
    <Box my="10px">
      <Heading size="md">{response.participant.name}</Heading>
      <Text>{response.response_text}</Text>
    </Box>
  );
}

function QuestionBlock({ question }: { question: PublicQuestion }) {
  return (
    <Box my="20px">
      <Heading>{question.question_text}</Heading>
      {question.responses.map((response) => {
        return (
          <ResponseBlock response={response} key={response.api_identifier} />
        );
      })}
    </Box>
  );
}

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
      <Container>
        {loop.questions.map((question) => {
          return (
            <QuestionBlock question={question} key={question.api_identifier} />
          );
        })}
      </Container>
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
