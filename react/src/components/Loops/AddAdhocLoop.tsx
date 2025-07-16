import {
    Button,
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
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import { AxiosError } from "axios";
import { AddNextLetterLettersLetterLetterTypePostError } from "../../client";
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
    groupApiId: string;
};

const AddAdhocLoop = ({ isOpen, onClose, groupApiId }: AddAdhocLoopProps) => {
    const queryClient = useQueryClient();
    const showToast = useCustomToast();
    let defaultDate = new Date();
    defaultDate.setUTCDate(defaultDate.getDate() + 7); // Default to 1 week from now
    defaultDate.setUTCHours(21);
    defaultDate.setUTCMinutes(0);
    defaultDate.setUTCSeconds(0);
    defaultDate.setUTCMilliseconds(0);

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
                    query: { group_api_id: groupApiId },
                }),
            });
        },
    });

    const onSubmit: SubmitHandler<AdhocLetterFormProps> = (data) => {
        mutation.mutate({
            path: { letter_type: "ADHOC" },
            body: {
                group_api_identifier: groupApiId,
                send_at:
                    data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt,
                title: data.title || null,
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
                        <Button variant="primary" type="submit" isLoading={isSubmitting}>
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