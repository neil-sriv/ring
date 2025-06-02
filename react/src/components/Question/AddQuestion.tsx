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
    useColorModeValue,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import { useRouter } from "@tanstack/react-router";
import { AxiosError } from "axios";
import {
    AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
    UserLinked,
} from "../../client";
import {
    addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
    readLetterLettersLetterLetterApiIdGetQueryKey,
    readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";

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
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
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

  const textColor = useColorModeValue("ui.dark", "ui.light");

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent 
          as="form" 
          onSubmit={handleSubmit(onSubmit)}
          bg="ui.glass.light.background"
          backdropFilter="blur(10px)"
          border="1px solid"
          borderColor="ui.glass.light.border"
          _dark={{
            bg: "ui.glass.dark.background",
            borderColor: "ui.glass.dark.border",
          }}
        >
          <ModalHeader color={textColor}>Add new question</ModalHeader>
          <ModalCloseButton color={textColor} />
          <ModalBody pb={6}>
            <FormControl>
              <Textarea
                id="questionText"
                {...register("questionText", {
                  required: "Question text is required.",
                })}
                bg="ui.glass.light.background"
                borderColor="ui.glass.light.border"
                _dark={{
                  bg: "ui.glass.dark.background",
                  borderColor: "ui.glass.dark.border",
                }}
                _hover={{
                  borderColor: "ui.primary",
                }}
                _focus={{
                  borderColor: "ui.primary",
                  boxShadow: "0 0 0 1px var(--chakra-colors-ui-primary)",
                }}
                placeholder="Enter your question here..."
                minH="100px"
              />
              {errors.questionText && (
                <FormErrorMessage>
                  {errors.questionText.message}
                </FormErrorMessage>
              )}
            </FormControl>
          </ModalBody>

          <ModalFooter gap={3}>
            <Button 
              variant="primary" 
              type="submit" 
              isLoading={isSubmitting}
              _hover={{ 
                opacity: 0.9,
                bg: "ui.primary",
              }}
              transition="all 0.2s ease-in-out"
            >
              Save
            </Button>
            <Button 
              onClick={onClose}
              variant="glass"
            >
              Cancel
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default AddQuestion;
