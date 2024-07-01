import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import AddQuestion from "./AddQuestion";
import { PublicLetter } from "../../client/models";

type QuestionNavProps = {
  loop: PublicLetter;
};

function QuestionNav(props: QuestionNavProps): JSX.Element {
  const addQuestionModal = useDisclosure();
  const enabled = true;

  const onClick = (): void => {
    enabled ? addQuestionModal.onOpen() : null;
  };
  return (
    <>
      <Flex py={8} gap={4}>
        <Button
          variant="primary"
          gap={1}
          fontSize={{ base: "sm", md: "inherit" }}
          onClick={() => onClick()}
          isDisabled={!enabled}
        >
          <Icon as={FaPlus} />{" "}
          {enabled ? "Add new question" : "Loop in progress"}
        </Button>
        <AddQuestion
          isOpen={addQuestionModal.isOpen}
          onClose={addQuestionModal.onClose}
          loopApiId={props.loop.api_identifier}
        />
      </Flex>
    </>
  );
}

export default QuestionNav;
