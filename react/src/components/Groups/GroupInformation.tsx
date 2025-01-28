import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  GroupLinked,
  GroupUpdate,
  UpdateGroupPartiesGroupGroupApiIdPatchError,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { useRouter } from "@tanstack/react-router";
import { updateGroupPartiesGroupGroupApiIdPatchMutation } from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

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
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, isDirty },
  } = useForm<GroupLinked>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group.name,
    },
  });

  const toggleEditMode = () => {
    setEditMode(!editMode);
  };

  const mutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "Group updated successfully.", "success");
    },
    onError: (err: AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: async () => {
      queryClient.invalidateQueries({ queryKey: ["group", groupId] });
      router.invalidate();
      await queryClient.refetchQueries({ queryKey: ["group", groupId] });
    },
  });

  const onSubmit: SubmitHandler<GroupUpdate> = async (data) => {
    mutation.mutate({
      body: data,
      path: { group_api_id: group.api_identifier },
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
          Group Information
        </Heading>
        <Box
          w={{ sm: "full", md: "50%" }}
          as="form"
          onSubmit={handleSubmit(onSubmit)}
        >
          <FormControl>
            <FormLabel color={color} htmlFor="name">
              Full name
            </FormLabel>
            {editMode ? (
              <Input
                id="name"
                {...register("name", { maxLength: 30 })}
                type="text"
                size="md"
              />
            ) : (
              <Text
                size="md"
                // py={2}
                color={!group.name ? "ui.dim" : "inherit"}
              >
                {group.name || "N/A"}
              </Text>
            )}
          </FormControl>
          <FormControl mt={4}>
            <FormLabel color={color} htmlFor="admin">
              Admin
            </FormLabel>
            <Text
              size="md"
              // py={2}
              color={!group.admin.name ? "ui.dim" : "inherit"}
            >
              {group.admin.name}
            </Text>
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
