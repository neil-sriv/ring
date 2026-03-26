import {
    Button,
    Checkbox,
    FormControl,
    FormErrorMessage,
    FormLabel,
    Input,
    Modal,
    ModalBody,
    ModalCloseButton,
    ModalContent,
    ModalFooter,
    ModalHeader,
    ModalOverlay,
    Stack,
    Text,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { type SubmitHandler, useForm } from "react-hook-form";

import { AxiosError } from "axios";
import {
    AddNextLetterLettersLetterLetterTypePostError,
    GroupLinked,
} from "../../client";
import {
    addNextLetterLettersLetterLetterTypePostMutation,
    listLettersLettersLettersGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";
import { toISOLocal } from "../../util/misc";

type AdhocLetterFormProps = {
    title: string;
    sendAt: Date | string;
};

type AddAdhocLoopProps = {
    isOpen: boolean;
    onClose: () => void;
    group: GroupLinked;
};

const AddAdhocLoop = ({ isOpen, onClose, group }: AddAdhocLoopProps) => {
    const queryClient = useQueryClient();
    const showToast = useCustomToast();
    let defaultDate = new Date();
    defaultDate.setUTCDate(defaultDate.getDate() + 7); // Default to 1 week from now
    defaultDate.setUTCHours(21);
    defaultDate.setUTCMinutes(0);
    defaultDate.setUTCSeconds(0);
    defaultDate.setUTCMilliseconds(0);

    const [responderIds, setResponderIds] = useState<string[]>(() =>
        group.members.map((m) => m.api_identifier),
    );

    useEffect(() => {
        setResponderIds(group.members.map((m) => m.api_identifier));
    }, [group.api_identifier, group.members]);

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors, isSubmitting },
    } = useForm<AdhocLetterFormProps>({
        mode: "onBlur",
        criteriaMode: "all",
        defaultValues: {
            title: "",
            sendAt: defaultDate.toISOString().slice(0, 16),
        },
    });

    const mutation = useMutation({
        ...addNextLetterLettersLetterLetterTypePostMutation(),
        onSuccess: () => {
            showToast("Success!", "Adhoc loop created successfully.", "success");
            reset();
            onClose();
        },
        onError: (err: AxiosError<AddNextLetterLettersLetterLetterTypePostError>) => {
            const errDetail =
                err.response?.data.detail || "no error detail, please contact support";
            showToast("Something went wrong.", `${errDetail}`, "error");
        },
        onSettled: () => {
            queryClient.invalidateQueries({
                queryKey: listLettersLettersLettersGetQueryKey({
                    query: { group_api_id: group.api_identifier },
                }),
            });
        },
    });

    function toggleResponder(apiId: string): void {
        setResponderIds((prev) =>
            prev.includes(apiId)
                ? prev.filter((id) => id !== apiId)
                : [...prev, apiId],
        );
    }

    const onSubmit: SubmitHandler<AdhocLetterFormProps> = (data) => {
        const allIds = group.members.map((m) => m.api_identifier);
        const isEveryone =
            responderIds.length === allIds.length &&
            allIds.every((id) => responderIds.includes(id));
        if (!isEveryone && responderIds.length === 0) {
            return;
        }
        mutation.mutate({
            path: { letter_type: "ADHOC" },
            body: {
                group_api_identifier: group.api_identifier,
                send_at:
                    data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt,
                title: data.title || null,
                responder_api_identifiers: isEveryone ? [] : responderIds,
            },
        });
    };

    return (
        <>
            <Modal
                isOpen={isOpen}
                onClose={onClose}
                size={{ base: "sm", md: "md" }}
                isCentered
            >
                <ModalOverlay />
                <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
                    <ModalHeader>Create Adhoc Loop</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody pb={6}>
                        <FormControl mb={4}>
                            <FormLabel htmlFor="title">Title (Optional)</FormLabel>
                            <Input
                                id="title"
                                {...register("title", {
                                    maxLength: {
                                        value: 100,
                                        message: "Title must be less than 100 characters",
                                    },
                                })}
                                placeholder="Enter a title for this adhoc loop"
                            />
                            {errors.title && (
                                <FormErrorMessage>{errors.title.message}</FormErrorMessage>
                            )}
                        </FormControl>

                        <FormControl mb={4} isInvalid={responderIds.length === 0}>
                            <FormLabel>Who can respond</FormLabel>
                            <Text fontSize="sm" color="ui.dim" mb={2}>
                                Everyone in the group can still add questions. Only
                                checked members can submit answers (default: everyone).
                            </Text>
                            <Stack spacing={2}>
                                {group.members.map((m) => (
                                    <Checkbox
                                        key={m.api_identifier}
                                        isChecked={responderIds.includes(
                                            m.api_identifier,
                                        )}
                                        onChange={() =>
                                            toggleResponder(m.api_identifier)
                                        }
                                    >
                                        {m.name || m.email}
                                    </Checkbox>
                                ))}
                            </Stack>
                            {responderIds.length === 0 && (
                                <FormErrorMessage>
                                    Select at least one responder.
                                </FormErrorMessage>
                            )}
                        </FormControl>

                        <FormControl isRequired>
                            <FormLabel htmlFor="sendAt">Send at</FormLabel>
                            <Input
                                id="sendAt"
                                {...register("sendAt", {
                                    required: "Send at is required.",
                                    valueAsDate: true,
                                })}
                                type="datetime-local"
                                min={toISOLocal(new Date()).slice(0, 16)}
                            />
                            {errors.sendAt && (
                                <FormErrorMessage>{errors.sendAt.message}</FormErrorMessage>
                            )}
                        </FormControl>
                    </ModalBody>

                    <ModalFooter gap={3}>
                        <Button
                            variant="primary"
                            type="submit"
                            isLoading={isSubmitting}
                            isDisabled={responderIds.length === 0}
                        >
                            Create Adhoc Loop
                        </Button>
                        <Button onClick={onClose}>Cancel</Button>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        </>
    );
};

export default AddAdhocLoop; 