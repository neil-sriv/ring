import {
    Button,
    Checkbox,
    Modal,
    ModalBody,
    ModalCloseButton,
    ModalContent,
    ModalFooter,
    ModalHeader,
    ModalOverlay,
    Text,
    VStack,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AxiosError } from "axios";
import { GroupLinked, PublicLetter } from "../../client";
import { SetLetterDesignatedRespondersLettersLetterLetterApiIdSetDesignatedRespondersPostError } from "../../client/types.gen";
import {
    readLetterLettersLetterLetterApiIdGetQueryKey,
    setLetterDesignatedRespondersLettersLetterLetterApiIdSetDesignatedRespondersPostMutation,
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";

interface LoopRespondersModalProps {
    isOpen: boolean;
    onClose: () => void;
    loop: PublicLetter;
    group: GroupLinked;
}

const LoopRespondersModal = ({ isOpen, onClose, loop, group }: LoopRespondersModalProps) => {
    const queryClient = useQueryClient();
    const showToast = useCustomToast();

    const hasDesignatedResponders = loop.designated_responders.length > 0;

    const [selectedResponders, setSelectedResponders] = useState<Set<string>>(
        () => {
            if (hasDesignatedResponders) {
                return new Set(loop.designated_responders.map((r) => r.api_identifier));
            }
            return new Set(group.members.map((m) => m.api_identifier));
        }
    );

    const isAllMembers = selectedResponders.size === group.members.length;

    const mutation = useMutation({
        ...setLetterDesignatedRespondersLettersLetterLetterApiIdSetDesignatedRespondersPostMutation(),
        onSuccess: () => {
            showToast("Success!", "Responders updated successfully.", "success");
            onClose();
        },
        onError: (
            err: AxiosError<SetLetterDesignatedRespondersLettersLetterLetterApiIdSetDesignatedRespondersPostError>
        ) => {
            const errDetail =
                err.response?.data.detail || "no error detail, please contact support";
            showToast("Something went wrong.", `${errDetail}`, "error");
        },
        onSettled: () => {
            queryClient.invalidateQueries({
                queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
                    path: { letter_api_id: loop.api_identifier },
                }),
            });
        },
    });

    function handleToggle(apiIdentifier: string): void {
        setSelectedResponders((prev) => {
            const next = new Set(prev);
            if (next.has(apiIdentifier)) {
                if (next.size <= 1) {
                    return next;
                }
                next.delete(apiIdentifier);
            } else {
                next.add(apiIdentifier);
            }
            return next;
        });
    }

    function handleSelectAll(): void {
        setSelectedResponders(new Set(group.members.map((m) => m.api_identifier)));
    }

    function handleSave(): void {
        const responderIds = isAllMembers ? [] : Array.from(selectedResponders);
        mutation.mutate({
            body: { responder_api_identifiers: responderIds },
            path: { letter_api_id: loop.api_identifier },
        });
    }

    return (
        <Modal isOpen={isOpen} onClose={onClose} size={{ base: "sm", md: "md" }} isCentered>
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Set Loop Responders</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                    <Text fontSize="sm" color="gray.500" mb={4}>
                        Select which members can respond to this loop.
                        Everyone else will still receive the loop email and can ask questions.
                    </Text>
                    <Button size="xs" variant="ghost" onClick={handleSelectAll} mb={2}>
                        Select All (reset to default)
                    </Button>
                    <VStack align="stretch" spacing={1}>
                        {group.members.map((member) => (
                            <Checkbox
                                key={member.api_identifier}
                                isChecked={selectedResponders.has(member.api_identifier)}
                                onChange={() => handleToggle(member.api_identifier)}
                                size="sm"
                            >
                                {member.name} ({member.email})
                            </Checkbox>
                        ))}
                    </VStack>
                </ModalBody>
                <ModalFooter gap={3}>
                    <Button
                        variant="primary"
                        onClick={handleSave}
                        isLoading={mutation.isPending}
                    >
                        Save
                    </Button>
                    <Button onClick={onClose}>Cancel</Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default LoopRespondersModal;
