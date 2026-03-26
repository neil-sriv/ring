import {
  Box,
  Button,
  Checkbox,
  Container,
  Flex,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Heading,
  Input,
  List,
  Stack,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  Controller,
  type SubmitHandler,
  useFieldArray,
  useForm,
} from "react-hook-form";

import { GroupLinked, UserLinked } from "../../client";
import {
  ReplaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostError,
  ReplaceGroupResponderAllowlistPartiesGroupGroupApiIdReplaceResponderAllowlistPostError,
  UpdateGroupPartiesGroupGroupApiIdPatchError,
} from "../../client/types.gen";
import useCustomToast from "../../hooks/useCustomToast";
import { useRouter } from "@tanstack/react-router";
import { FiPlus } from "react-icons/fi";
import {
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
  replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation,
  replaceGroupResponderAllowlistPartiesGroupGroupApiIdReplaceResponderAllowlistPostMutation,
  updateGroupPartiesGroupGroupApiIdPatchMutation,
} from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

type QuestionField = {
  question_text: string;
};

type FormData = {
  questions: QuestionField[];
  cycle_length: number;
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
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  );

  if (group === undefined) {
    return null;
  }

  const isGroupAdmin =
    currentUser?.api_identifier === group.admin.api_identifier;

  const [cyclicResponderIds, setCyclicResponderIds] = useState<string[]>(() =>
    group.responder_allowlist.length === 0
      ? group.members.map((m) => m.api_identifier)
      : group.responder_allowlist.map((m) => m.api_identifier),
  );

  useEffect(() => {
    setCyclicResponderIds(
      group.responder_allowlist.length === 0
        ? group.members.map((m) => m.api_identifier)
        : group.responder_allowlist.map((m) => m.api_identifier),
    );
  }, [
    group.api_identifier,
    group.responder_allowlist,
    group.members,
  ]);

  const router = useRouter();
  const {
    handleSubmit,
    reset,
    control,
    register,
    formState: { isSubmitting, isDirty, errors },
  } = useForm<FormData>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      questions: group.default_questions.map((question) => ({
        question_text: question.question_text,
      })),
      cycle_length: group.cycle_length,
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

  const defaultQuestionsMutation = useMutation({
    ...replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Loop settings updated successfully.", "success");
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

  const cyclicRespondersMutation = useMutation({
    ...replaceGroupResponderAllowlistPartiesGroupGroupApiIdReplaceResponderAllowlistPostMutation(),
    onSuccess: () => {
      showToast(
        "Success!",
        "Cyclic loop responders updated.",
        "success",
      );
    },
    onError: (
      err: AxiosError<ReplaceGroupResponderAllowlistPartiesGroupGroupApiIdReplaceResponderAllowlistPostError>,
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

  const cycleUpdateMutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "Cycle length updated successfully.", "success");
    },
    onError: (err: AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>) => {
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

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    if (data.cycle_length !== group.cycle_length) {
      cycleUpdateMutation.mutate({
        body: { cycle_length: data.cycle_length },
        path: { group_api_id: groupId },
      });
    }

    defaultQuestionsMutation.mutate({
      body: {
        questions: data.questions.map((question) => question.question_text),
      },
      path: { group_api_id: groupId },
    });

    toggleEditMode();
  };

  const onCancel = () => {
    reset();
    toggleEditMode();
  };

  function toggleCyclicResponder(apiId: string): void {
    setCyclicResponderIds((prev) =>
      prev.includes(apiId)
        ? prev.filter((id) => id !== apiId)
        : [...prev, apiId],
    );
  }

  function saveCyclicResponders(): void {
    if (!group) {
      return;
    }
    if (cyclicResponderIds.length === 0) {
      showToast(
        "Invalid selection",
        "Select at least one person who can respond, or reset to everyone.",
        "error",
      );
      return;
    }
    const allMemberIds = group.members.map((m) => m.api_identifier);
    const isEveryone =
      cyclicResponderIds.length === allMemberIds.length &&
      allMemberIds.every((id) => cyclicResponderIds.includes(id));
    cyclicRespondersMutation.mutate({
      path: { group_api_id: groupId },
      body: {
        user_api_identifiers: isEveryone ? [] : cyclicResponderIds,
      },
    });
  }

  return (
    <>
      <Container maxW="full">
        <Heading size="sm" py={4}>
          Loop Settings
        </Heading>
        {isGroupAdmin && (
          <Box mb={8}>
            <Heading size="xs" py={2}>
              Who can respond (cyclic loops)
            </Heading>
            <Text fontSize="sm" color={color} mb={3}>
              Everyone in the group still receives loop emails. Only checked
              members can submit responses on recurring loops unless you leave
              everyone selected (default).
            </Text>
            <Stack spacing={2} mb={3}>
              {group.members.map((m) => (
                <Checkbox
                  key={m.api_identifier}
                  isChecked={cyclicResponderIds.includes(m.api_identifier)}
                  onChange={() => toggleCyclicResponder(m.api_identifier)}
                >
                  {m.name || m.email}
                </Checkbox>
              ))}
            </Stack>
            <Button
              variant="outline"
              size="sm"
              onClick={saveCyclicResponders}
              isLoading={cyclicRespondersMutation.isPending}
            >
              Save responders
            </Button>
          </Box>
        )}
        <Box
          w={{ sm: "full", md: "50%" }}
          as="form"
          onSubmit={handleSubmit(onSubmit)}
        >
          <FormControl isInvalid={!!errors.cycle_length}>
            <FormLabel color={color} htmlFor="cycle_length">
              Loop Cycle (days)
            </FormLabel>
            {editMode ? (
              <Input
                id="cycle_length"
                {...register("cycle_length", {
                  valueAsNumber: true,
                  required: "Cycle length is required",
                  min: {
                    value: 1,
                    message: "Cycle length must be greater than 0",
                  },
                })}
                type="number"
                size="md"
              />
            ) : (
              <Text size="md" py={2} color={color}>
                {group.cycle_length} days
              </Text>
            )}
            <FormErrorMessage>
              {errors.cycle_length && errors.cycle_length.message}
            </FormErrorMessage>
          </FormControl>
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
              onClick={editMode ? undefined : toggleEditMode}
              type={editMode ? "submit" : "button"}
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
