import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import AddQuestion from "./AddQuestion";
import { GroupLinked, PublicLetter, UserLinked } from "../../client/models";
import EditLetter from "../Loops/EditLoop";
import { useQueryClient } from "@tanstack/react-query";

type QuestionNavProps = {
  loop: PublicLetter;
  group: GroupLinked;
};

function QuestionNav(props: QuestionNavProps): JSX.Element {
  const editLoopModal = useDisclosure();
  const addQuestionModal = useDisclosure();
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);

  const onClickEdit = (): void => {
    editLoopModal.onOpen();
  };

  const onClickAddQuestion = (): void => {
    addQuestionModal.onOpen();
  };
  return (
    <>
      <Flex py={8} gap={4}>
        {props.group.admin.api_identifier === currentUser?.api_identifier && (
          <Button
            variant="primary"
            gap={1}
            fontSize={{ base: "sm", md: "inherit" }}
            onClick={() => onClickEdit()}
            isDisabled={
              props.group.admin.api_identifier !== currentUser?.api_identifier
            }
          >
            Edit Loop
          </Button>
        )}
        {props.loop.status === "UPCOMING" && (
          <Button
            variant="primary"
            gap={1}
            fontSize={{ base: "sm", md: "inherit" }}
            onClick={() => onClickAddQuestion()}
          >
            <Icon as={FaPlus} />{" "}
            {/* {enabled ? "Add new question" : "Loop in progress"} */}
            Add new question
          </Button>
        )}
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
