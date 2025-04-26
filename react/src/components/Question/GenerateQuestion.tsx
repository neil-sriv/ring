import {
    Button,
    FormControl,
    FormErrorMessage,
    Modal,
    ModalBody,
    ModalCloseButton,
    ModalContent,
    ModalFooter,
    ModalHeader,
    ModalOverlay,
    Textarea,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import { useRouter } from "@tanstack/react-router";
import { AxiosError } from "axios";
import { useState } from "react";
import {
    AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
    UserLinked,
} from "../../client";
import {
    addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
    generateQuestionLettersLetterLetterApiIdGenerateQuestionPostMutation,
    readLetterLettersLetterLetterApiIdGetQueryKey,
    readUserMePartiesMeGetQueryKey
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";

type QuestionFormProps = {
    questionPrompt: string;
};

interface GenerateQuestionProps {
    isOpen: boolean;
    onClose: () => void;
    loopApiId: string;
}

const GenerateQuestion = ({ isOpen, onClose, loopApiId }: GenerateQuestionProps) => {
    const queryClient = useQueryClient();
    const currentUser = queryClient.getQueryData<UserLinked>(
        readUserMePartiesMeGetQueryKey()
    );
    const router = useRouter();
    const showToast = useCustomToast();
    const [generatedQuestion, setGeneratedQuestion] = useState<string>("");
    const {
        register,
        handleSubmit,
        reset,
        formState: { errors, isSubmitting },
    } = useForm<QuestionFormProps>({
        mode: "onBlur",
        criteriaMode: "all",
    });

    const generateQuestionMutation = useMutation({
        ...generateQuestionLettersLetterLetterApiIdGenerateQuestionPostMutation({
            path: { letter_api_id: loopApiId },
        }),
        onSuccess: (data) => {
            setGeneratedQuestion(data.generated_text);
            showToast("Success!", "Question generated successfully.", "success");
        },
        onError: (
            err: AxiosError<AddQuestionLettersLetterLetterApiIdAddQuestionPostError>
        ) => {
            const errDetail =
                err.response?.data.detail || "no error detail, please contact support";
            showToast("Something went wrong.", `${errDetail}`, "error");
        },
    });

    const addQuestionMutation = useMutation({
        ...addQuestionLettersLetterLetterApiIdAddQuestionPostMutation(),
        onSuccess: () => {
            showToast("Success!", "New question created successfully.", "success");
            reset();
            onClose();
        },
        onError: (
            err: AxiosError<AddQuestionLettersLetterLetterApiIdAddQuestionPostError>
        ) => {
            const errDetail =
                err.response?.data.detail || "no error detail, please contact support";
            showToast("Something went wrong.", `${errDetail}`, "error");
        },
        onSettled: () => {
            queryClient.invalidateQueries({
                queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
                    path: { letter_api_id: loopApiId },
                }),
            });
            router.invalidate();
        },
    });

    const onGenerateQuestion: SubmitHandler<QuestionFormProps> = (data) => {
        generateQuestionMutation.mutate({
            body: {
                prompt: data.questionPrompt,
            },
            path: { letter_api_id: loopApiId },
        });
    };

    const onSaveQuestion = () => {
        if (!generatedQuestion) {
            showToast("Error", "No question to save. Please generate a question first.", "error");
            return;
        }

        addQuestionMutation.mutate({
            body: {
                question_text: generatedQuestion,
                author_api_id: currentUser?.api_identifier || null,
            },
            path: { letter_api_id: loopApiId },
        });
    };

    const handleClose = () => {
        reset();
        setGeneratedQuestion("");
        onClose();
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={handleClose}
            size={{ base: "sm", md: "md" }}
            isCentered
        >
            <ModalOverlay />
            <ModalContent as="form" onSubmit={handleSubmit(onGenerateQuestion)}>
                <ModalHeader>Generate question</ModalHeader>
                <ModalCloseButton />
                <ModalBody pb={6}>
                    <FormControl isInvalid={!!errors.questionPrompt}>
                        <Textarea
                            id="questionPrompt"
                            placeholder="Enter a prompt to generate a question..."
                            {...register("questionPrompt", {
                                required: "Question prompt is required.",
                            })}
                        />
                        {errors.questionPrompt && (
                            <FormErrorMessage>
                                {errors.questionPrompt.message}
                            </FormErrorMessage>
                        )}
                    </FormControl>
                    {generatedQuestion && (
                        <FormControl mt={4}>
                            <Textarea
                                id="generatedQuestion"
                                value={generatedQuestion}
                                readOnly
                                placeholder="Generated question will appear here..."
                                minH="100px"
                            />
                        </FormControl>
                    )}
                </ModalBody>

                <ModalFooter gap={3}>
                    <Button
                        type="submit"
                        isLoading={generateQuestionMutation.isPending}
                    >
                        Generate
                    </Button>
                    <Button
                        onClick={onSaveQuestion}
                        isLoading={addQuestionMutation.isPending}
                        isDisabled={!generatedQuestion}
                        variant="primary"
                    >
                        Save
                    </Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default GenerateQuestion;
