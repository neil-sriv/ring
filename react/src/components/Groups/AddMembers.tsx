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
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  AddMembersPartiesGroupGroupApiIdAddMembersPostError,
  type GroupLinked,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import {
  addMembersPartiesGroupGroupApiIdAddMembersPostMutation,
  listGroupsPartiesGroupsGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

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
          <ModalHeader>Add new members</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isInvalid={!!errors.member_emails}>
              <FormLabel htmlFor="name">New Member Emails</FormLabel>
              <Text>
                Enter the email addresses of the new members you want to add to
                this group. Separate multiple emails with a comma.
              </Text>
              <Input
                id="name"
                {...register("member_emails", {
                  required: "New member emails are required",
                })}
                type="text"
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
            >
              Save
            </Button>
            <Button onClick={onCancel}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default AddMembers;
