import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { FaPlus } from "react-icons/fa";
import { GroupLinked, MinimalLetter } from "../../client";
import {
    listLettersLettersLettersGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import AddAdhocLoop from "./AddAdhocLoop";

type AdhocLoopNavProps = {
    loops: MinimalLetter[];
    group: GroupLinked;
};

function AdhocLoopNav(props: AdhocLoopNavProps): JSX.Element {
    const addAdhocLoopModal = useDisclosure();
    const queryClient = useQueryClient();
    const router = useRouter();

    const onClick = (): void => {
        queryClient.invalidateQueries({
            queryKey: listLettersLettersLettersGetQueryKey({
                query: {
                    group_api_id: props.group.api_identifier,
                },
            }),
        });
        router.invalidate();
        addAdhocLoopModal.onOpen();
    };

    return (
        <>
            <Flex>
                <Button
                    variant="primary"
                    gap={1}
                    fontSize={{ base: "sm", md: "inherit" }}
                    onClick={() => onClick()}
                >
                    <Icon as={FaPlus} />
                    Create Adhoc Loop
                </Button>
                <AddAdhocLoop
                    isOpen={addAdhocLoopModal.isOpen}
                    onClose={addAdhocLoopModal.onClose}
                    group={props.group}
                />
            </Flex>
        </>
    );
}

export default AdhocLoopNav; 