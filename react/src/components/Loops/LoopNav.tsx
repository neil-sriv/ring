import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import AddLetter from "./AddLoop";
import { GroupLinked, PublicLetter, UserLinked } from "../../client";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { listLettersLettersLettersGetQueryKey } from "../../client/@tanstack/react-query.gen";

type LoopNavProps = {
  loops: PublicLetter[];
  group: GroupLinked;
};

function LoopNav(props: LoopNavProps): JSX.Element {
  const addLetterModal = useDisclosure();
  const enabled =
    props.loops.filter((loop) => loop.status === "UPCOMING").length === 0;
  const queryClient = useQueryClient();
  const router = useRouter();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);

  const onClick = (): void => {
    queryClient.invalidateQueries({
      queryKey: listLettersLettersLettersGetQueryKey({
        query: { group_api_id: props.group.api_identifier },
      }),
    });
    router.invalidate();
    enabled ? addLetterModal.onOpen() : null;
  };
  return (
    <>
      <Flex py={8} gap={4}>
        {props.group.admin.api_identifier === currentUser?.api_identifier && (
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
        )}
        <AddLetter
          isOpen={addLetterModal.isOpen}
          onClose={addLetterModal.onClose}
          groupApiId={props.group.api_identifier}
        />
      </Flex>
    </>
  );
}

export default LoopNav;
