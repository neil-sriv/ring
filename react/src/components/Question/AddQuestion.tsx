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

import {
  AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
  UserLinked,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { useRouter } from "@tanstack/react-router";
import {
  addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

type QuestionFormProps = {
  questionText: string;
};

interface AddQuestionProps {
  isOpen: boolean;
  onClose: () => void;
  loopApiId: string;
}

const AddQuestion = ({ isOpen, onClose, loopApiId }: AddQuestionProps) => {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);
  const router = useRouter();
  const showToast = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<QuestionFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
  });

  const mutation = useMutation({
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

  const onSubmit: SubmitHandler<QuestionFormProps> = (data) => {
    mutation.mutate({
      body: {
        question_text: data.questionText,
        author_api_id: currentUser!.api_identifier,
      },
      path: { letter_api_id: loopApiId },
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
          <ModalHeader>Add new question</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl>
              <Textarea
                id="questionText"
                {...register("questionText", {
                  required: "Question text is required.",
                })}
              />
              {errors.questionText && (
                <FormErrorMessage>
                  {errors.questionText.message}
                </FormErrorMessage>
              )}
            </FormControl>
          </ModalBody>

          <ModalFooter gap={3}>
            <Button variant="primary" type="submit" isLoading={isSubmitting}>
              Save
            </Button>
            <Button onClick={onClose}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default AddQuestion;
