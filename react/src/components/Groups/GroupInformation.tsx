import {
    Box,
    Button,
    Flex,
    Heading,
    Input,
    Text,
    useColorModeValue
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { type SubmitHandler, useForm } from "react-hook-form";

import { useRouter } from "@tanstack/react-router";
import { AxiosError } from "axios";
import {
    GroupLinked,
    GroupUpdate,
    UpdateGroupPartiesGroupGroupApiIdPatchError,
} from "../../client";
import {
    readGroupPartiesGroupGroupApiIdGetQueryKey,
    updateGroupPartiesGroupGroupApiIdPatchMutation,
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";

function GroupInformation({ groupId }: { groupId: string }) {
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
      reset();
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

  const textColor = useColorModeValue("ui.dark", "ui.light");
  const bgColor = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const borderColor = useColorModeValue("ui.glass.light.border", "ui.glass.dark.border");

  return (
    <Box
      p={6}
      bg={bgColor}
      backdropFilter="blur(10px)"
      border="1px solid"
      borderColor={borderColor}
      borderRadius="lg"
      boxShadow="sm"
    >
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="md" color={textColor}>Group Information</Heading>
        <Button
          variant="glass"
          onClick={toggleEditMode}
          _hover={{ 
            opacity: 0.9,
            bg: "ui.primary",
          }}
          transition="all 0.2s ease-in-out"
        >
          Edit
        </Button>
      </Flex>
      
      <Box>
        <Text color={textColor} fontWeight="medium" mb={2}>Name</Text>
        {editMode ? (
          <Input
            id="name"
            {...register("name", { maxLength: 30 })}
            type="text"
            size="md"
          />
        ) : (
          <Text color={textColor} mb={4}>{group.name || "N/A"}</Text>
        )}
        
        <Text color={textColor} fontWeight="medium" mb={2}>Description</Text>
        <Text color={textColor} mb={4}>{group.description || "No description provided"}</Text>
        
        <Text color={textColor} fontWeight="medium" mb={2}>Created At</Text>
        <Text color={textColor}>{new Date(group.created_at).toLocaleDateString()}</Text>
      </Box>
    </Box>
  );
}

export default GroupInformation;
