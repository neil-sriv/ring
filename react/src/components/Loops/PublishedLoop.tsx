import { Box, Button, Container, Flex, Text, useColorModeValue } from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { PublicLetter, UserLinked } from "../../client";
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen";
import LateAnswerQuestion from "../Question/LateAnswerQuestion";
import PublishedQuestion from "../Question/PublishedQuestion";

function PublishedLoop({ loop }: { loop: PublicLetter }) {
  const [showLateAnswers, setShowLateAnswers] = useState(false);
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );

  const textColor = useColorModeValue("ui.dark", "ui.light");
  const borderColor = useColorModeValue("gray.200", "gray.600");

  if (!currentUser) {
    return <Container maxW="full">Loading...</Container>;
  }

  // Get questions the user hasn't answered
  const unansweredQuestions = loop.questions.filter((question) => {
    return !question.responses.some(
      (response) => response.participant.api_identifier === currentUser.api_identifier
    );
  });

  const hasUnansweredQuestions = unansweredQuestions.length > 0;

  return (
    <Container maxW="full">
      {/* Late Answers Toggle */}
      {hasUnansweredQuestions && (
        <Box
          mb="6"
          p="4"
          border="1px"
          borderColor={borderColor}
          borderRadius="md"
          bg={useColorModeValue("blue.50", "blue.900")}
        >
          <Flex justify="space-between" align="center">
            <Box>
              <Text fontWeight="bold" color={textColor}>
                Late Answers Available
              </Text>
              <Text fontSize="sm" color={useColorModeValue("gray.600", "gray.300")}>
                You have {unansweredQuestions.length} question{unansweredQuestions.length !== 1 ? 's' : ''} you haven't answered yet.
              </Text>
            </Box>
            <Button
              colorScheme="blue"
              variant={showLateAnswers ? "solid" : "outline"}
              onClick={() => setShowLateAnswers(!showLateAnswers)}
            >
              {showLateAnswers ? "Hide Late Answers" : "Show Late Answers"}
            </Button>
          </Flex>
        </Box>
      )}

      {/* Late Answer Questions */}
      {showLateAnswers && hasUnansweredQuestions && (
        <Box mb="6">
          <Text fontSize="lg" fontWeight="bold" mb="4" color={textColor}>
            Questions You Haven't Answered:
          </Text>
          {unansweredQuestions.map((question) => (
            <LateAnswerQuestion
              key={question.api_identifier}
              question={question}
              loopApiId={loop.api_identifier}
            />
          ))}
        </Box>
      )}

      {/* All Questions (Published) */}
      <Box>
        <Text fontSize="lg" fontWeight="bold" mb="4" color={textColor}>
          All Questions and Responses:
        </Text>
        {loop.questions
          .sort(
            (a, b) =>
              new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )
          .map((question) => {
            return (
              <PublishedQuestion
                question={question}
                key={question.api_identifier}
                currentUserApiId={currentUser.api_identifier}
                letterSendAt={loop.send_at}
              />
            );
          })}
      </Box>
    </Container>
  );
}

export default PublishedLoop;
