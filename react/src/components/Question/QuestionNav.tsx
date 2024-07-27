import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import AddQuestion from "./AddQuestion";
import { PublicLetter } from "../../client/models";
import EditLetter from "../Loops/EditLoop";

type QuestionNavProps = {
  loop: PublicLetter;
};

function QuestionNav(props: QuestionNavProps): JSX.Element {
  const editLoopModal = useDisclosure();
  const addQuestionModal = useDisclosure();
  const enabled = true;

  const onClickEdit = (): void => {
    editLoopModal.onOpen();
  };

  const onClickAddQuestion = (): void => {
    enabled ? addQuestionModal.onOpen() : null;
  };
  return (
    <>
      <Flex py={8} gap={4}>
        <Button
          variant="primary"
          gap={1}
          fontSize={{ base: "sm", md: "inherit" }}
          onClick={() => onClickEdit()}
          isDisabled={!enabled}
        >
          Edit Loop
        </Button>
        <Button
          variant="primary"
          gap={1}
          fontSize={{ base: "sm", md: "inherit" }}
          onClick={() => onClickAddQuestion()}
          isDisabled={!enabled}
        >
          <Icon as={FaPlus} />{" "}
          {enabled ? "Add new question" : "Loop in progress"}
        </Button>
        <EditLetter
          isOpen={editLoopModal.isOpen}
          onClose={editLoopModal.onClose}
          loop={props.loop}
        />
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
