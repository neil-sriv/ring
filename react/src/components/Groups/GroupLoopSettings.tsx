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

import {
  type ApiError,
  GroupLinked,
  PartiesService,
  QuestionUnlinked,
  ReplaceDefaultQuestions,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { useRouter } from "@tanstack/react-router";

function GroupInformation({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient();
  const color = useColorModeValue("inherit", "ui.light");
  const showToast = useCustomToast();
  const [editMode, setEditMode] = useState(false);
  const group = queryClient.getQueryData<GroupLinked>(["group", groupId]);

  if (group === undefined) {
    return null;
  }

  const router = useRouter();
  const {
    handleSubmit,
    reset,
    control,
    formState: { isSubmitting, isDirty },
  } = useForm<{ questions: QuestionUnlinked[] }>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      questions: group.default_questions,
    },
  });

  const { fields, remove } = useFieldArray({
    control,
    name: "questions",
  });

  const toggleEditMode = () => {
    setEditMode(!editMode);
  };

  const mutation = useMutation({
    mutationFn: (data: ReplaceDefaultQuestions) =>
      PartiesService.replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPost(
        {
          groupApiId: groupId,
          requestBody: data,
        }
      ),
    onSuccess: () => {
      showToast("Success!", "Loop settings updated successfully.", "success");
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail;
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: async (group) => {
      queryClient.invalidateQueries({ queryKey: ["group", groupId] });
      router.invalidate();
      await queryClient.refetchQueries({ queryKey: ["group", groupId] });
      reset({ questions: group?.default_questions });
    },
  });

  const onSubmit: SubmitHandler<{ questions: QuestionUnlinked[] }> = async (
    data
  ) => {
    mutation.mutate({
      questions: data.questions.map((question) => question.question_text),
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
                          render={({ field }) => <Input {...field} size="md" />}
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

export default GroupInformation;
