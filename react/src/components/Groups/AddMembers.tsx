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
    Text,
    useColorModeValue,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import { AxiosError } from "axios";
import {
    AddMembersPartiesGroupGroupApiIdAddMembersPostError,
    type GroupLinked,
} from "../../client";
import {
    addMembersPartiesGroupGroupApiIdAddMembersPostMutation,
    listGroupsPartiesGroupsGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";

interface AddMembersProps {
  group: GroupLinked;
  isOpen: boolean;
  onClose: () => void;
}

type AddMembersFormType = {
  member_emails: string;
};

const AddMembers = ({ group, isOpen, onClose }: AddMembersProps) => {
  const queryClient = useQueryClient();
  const showToast = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<AddMembersFormType>({
    mode: "onBlur",
    criteriaMode: "all",
  });

  const mutation = useMutation({
    ...addMembersPartiesGroupGroupApiIdAddMembersPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Group updated successfully.", "success");
      reset();
      onClose();
    },
    onError: (
      err: AxiosError<AddMembersPartiesGroupGroupApiIdAddMembersPostError>
    ) => {
      console.log(err);
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: listGroupsPartiesGroupsGetQueryKey({
          query: { user_api_id: group.api_identifier },
        }),
      });
    },
  });

  const onSubmit: SubmitHandler<AddMembersFormType> = async (data) => {
    const memberEmails = data.member_emails
      .split(",")
      .map((email) => email.trim());
    mutation.mutate({
      body: { member_emails: memberEmails },
      path: { group_api_id: group.api_identifier },
    });
  };

  const onCancel = () => {
    reset();
    onClose();
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
          <ModalHeader color={textColor}>Add new members</ModalHeader>
          <ModalCloseButton color={textColor} />
          <ModalBody pb={6}>
            <FormControl isInvalid={!!errors.member_emails}>
              <FormLabel htmlFor="name" color={textColor}>New Member Emails</FormLabel>
              <Text color={textColor}>
                Enter the email addresses of the new members you want to add to
                this group. Separate multiple emails with a comma.
              </Text>
              <Input
                id="name"
                {...register("member_emails", {
                  required: "New member emails are required",
                })}
                type="text"
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
              />
              {errors.member_emails && (
                <FormErrorMessage>
                  {errors.member_emails.message}
                </FormErrorMessage>
              )}
            </FormControl>
            {/* <FormControl mt={4}>
              <FormLabel htmlFor="description">Description</FormLabel>
              <Input
                id="description"
                {...register("description")}
                placeholder="Description"
                type="text"
              />
            </FormControl> */}
          </ModalBody>
          <ModalFooter gap={3}>
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
              isDisabled={!isDirty}
              _hover={{ 
                opacity: 0.9,
                bg: "ui.primary",
              }}
              transition="all 0.2s ease-in-out"
            >
              Save
            </Button>
            <Button 
              onClick={onCancel}
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

export default AddMembers;
