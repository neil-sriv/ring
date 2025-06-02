import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import { useQueryClient } from "@tanstack/react-query";
import { GroupLinked, PublicLetter, UserLinked } from "../../client";
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen";
import AddQuestion from "./AddQuestion";
import GenerateQuestion from "./GenerateQuestion";

type QuestionNavProps = {
  loop: PublicLetter;
  group: GroupLinked;
};

function QuestionNav(props: QuestionNavProps): JSX.Element {
  const addQuestionModal = useDisclosure();
  const generateQuestionModal = useDisclosure();
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );

  const onClickAddQuestion = (): void => {
    addQuestionModal.onOpen();
  };

  const onClickGenerateQuestion = (): void => {
    generateQuestionModal.onOpen();
  };
  return (
    <>
      <Flex gap={4} wrap="wrap">
        {props.loop.status === "UPCOMING" && (
          <Button
            variant="primary"
            gap={1}
            fontSize={{ base: "sm", md: "inherit" }}
            onClick={() => onClickAddQuestion()}
            whiteSpace="normal"
            textAlign="left"
            height="auto"
            py={2}
            _hover={{ transform: "translateY(-2px)" }}
            transition="all 0.2s"
          >
            <Icon as={FaPlus} />{" "}
            Add new question
          </Button>
        )}
        {props.loop.status === "UPCOMING" && (
          <Button
            variant="primary"
            gap={1}
            fontSize={{ base: "sm", md: "inherit" }}
            onClick={() => onClickGenerateQuestion()}
            whiteSpace="normal"
            textAlign="left"
            height="auto"
            py={2}
            _hover={{ transform: "translateY(-2px)" }}
            transition="all 0.2s"
          >
            <Icon as={FaPlus} />{" "}
            Ask ChatGPT to generate a question.
          </Button>
        )}

        <AddQuestion
          isOpen={addQuestionModal.isOpen}
          onClose={addQuestionModal.onClose}
          loopApiId={props.loop.api_identifier}
        />
        <GenerateQuestion
          isOpen={generateQuestionModal.isOpen}
          onClose={generateQuestionModal.onClose}
          loopApiId={props.loop.api_identifier}
        />
      </Flex>
    </>
  );
}

export default QuestionNav;
