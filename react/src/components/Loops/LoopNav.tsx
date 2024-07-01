import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import AddLetter from "./AddLoop";
import { PublicLetter } from "../../client/models";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";

type LoopNavProps = {
  loops: PublicLetter[];
  groupId: string;
};

function LoopNav(props: LoopNavProps): JSX.Element {
  const addLetterModal = useDisclosure();
  const enabled =
    props.loops.filter((loop) => loop.status === "IN_PROGRESS").length === 0;
  const queryClient = useQueryClient();
  const router = useRouter();

  const onClick = (): void => {
    queryClient.invalidateQueries({ queryKey: ["loops", props.groupId] });
    router.invalidate();
    enabled ? addLetterModal.onOpen() : null;
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
          {enabled ? "Start Next Loop" : "Loop in progress"}
        </Button>
        <AddLetter
          isOpen={addLetterModal.isOpen}
          onClose={addLetterModal.onClose}
          groupApiId={props.groupId}
        />
      </Flex>
    </>
  );
}

export default LoopNav;
