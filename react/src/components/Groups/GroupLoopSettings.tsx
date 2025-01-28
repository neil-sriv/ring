import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  List,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  Controller,
  type SubmitHandler,
  useFieldArray,
  useForm,
} from "react-hook-form";

import { GroupLinked } from "../../client";
import { ReplaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostError } from "../../client/types.gen";
import useCustomToast from "../../hooks/useCustomToast";
import { useRouter } from "@tanstack/react-router";
import { FiPlus } from "react-icons/fi";
import {
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation,
} from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

type QuestionField = {
  question_text: string;
};

function GroupLoopSettings({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient();
  const color = useColorModeValue("inherit", "ui.light");
  const showToast = useCustomToast();
  const [editMode, setEditMode] = useState(false);
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    })
  );

  if (group === undefined) {
    return null;
  }

  const router = useRouter();
  const {
    handleSubmit,
    reset,
    control,
    register,
    formState: { isSubmitting, isDirty, errors },
  } = useForm<{ questions: QuestionField[] }>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      questions: group.default_questions.map((question) => ({
        question_text: question.question_text,
      })),
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "questions",
    rules: {
      validate: (value) =>
        value.every((question) => question.question_text.length > 0) ||
        "Question cannot be empty.",
    },
  });

  const toggleEditMode = () => {
    setEditMode(!editMode);
  };

  const mutation = useMutation({
    ...replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Loop settings updated successfully.", "success");
      reset();
    },
    onError: (
      err: AxiosError<ReplaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostError>
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: async () => {
      queryClient.invalidateQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: groupId },
        }),
      });
      router.invalidate();
      await queryClient.refetchQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: groupId },
        }),
      });
    },
  });

  const onSubmit: SubmitHandler<{ questions: QuestionField[] }> = async (
    data
  ) => {
    mutation.mutate({
      body: {
        questions: data.questions.map((question) => question.question_text),
      },
      path: { group_api_id: groupId },
    });
  };

  const onCancel = () => {
    reset();
    toggleEditMode();
  };

  return (
    <>
      <Container maxW="full">
        <Heading size="sm" py={4}>
          Loop Settings
        </Heading>
        <Box
          w={{ sm: "full", md: "50%" }}
          as="form"
          onSubmit={handleSubmit(onSubmit)}
        >
          {/* <FormControl>
            <FormLabel color={color} htmlFor="cycle">
              Loop Cycle
            </FormLabel>
            {editMode ? (
              <Input
                id="cycle"
                {...register("cycle", { valueAsNumber: true })}
                type="number"
                size="md"
              />
            ) : (
              <Text
                size="md"
                py={2}
                color={!group.cycle ? "ui.dim" : "inherit"}
              >
                {group.cycle ?? "Not set"}
              </Text>
            )}
          </FormControl> */}
          <FormControl mt={4}>
            <FormLabel color={color} htmlFor="defaultQuestions">
              Default Questions
            </FormLabel>
            <List>
              {fields.map((field, index) => (
                <Box key={field.id}>
                  <Flex>
                    {editMode ? (
                      <>
                        <Controller
                          control={control}
                          name={`questions.${index}.question_text`}
                          render={({ field }) => (
                            <Input
                              {...register(`questions.${index}.question_text`)}
                              {...field}
                              size="md"
                            />
                          )}
                        />
                        <Button
                          onClick={() => remove(index)}
                          ml={2}
                          size="sm"
                          variant="outline"
                        >
                          Remove
                        </Button>
                      </>
                    ) : (
                      <Text size="md" py={2} color="inherit">
                        {field.question_text}
                      </Text>
                    )}
                  </Flex>
                </Box>
              ))}
              {editMode && (
                <Button
                  type="button"
                  onClick={() => append({ question_text: "" })}
                >
                  <FiPlus />
                </Button>
              )}
              {errors.questions?.root && (
                <Text color="ui.error" fontSize="sm">
                  {errors.questions.root?.message}
                </Text>
              )}
            </List>
          </FormControl>
          <Flex mt={4} gap={3}>
            <Button
              variant="primary"
              onClick={toggleEditMode}
              type={editMode ? "button" : "submit"}
              isLoading={editMode ? isSubmitting : false}
              isDisabled={editMode ? !isDirty : false}
            >
              {editMode ? "Save" : "Edit"}
            </Button>
            {editMode && (
              <Button onClick={onCancel} isDisabled={isSubmitting}>
                Cancel
              </Button>
            )}
          </Flex>
        </Box>
      </Container>
    </>
  );
}

export default GroupLoopSettings;
