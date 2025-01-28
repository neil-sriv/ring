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
  addMembersPartiesGroupGroupApiIdAddMembersPost,
  AddMembersPartiesGroupGroupApiIdAddMembersPostError,
  AddMembers as AddMembersType,
  type GroupLinked,
} from "../../client";
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
    mutationFn: (data: AddMembersType) =>
      addMembersPartiesGroupGroupApiIdAddMembersPost({
        path: {
          group_api_id: group.api_identifier,
        },
        body: data,
      }),
    onSuccess: () => {
      showToast("Success!", "Group updated successfully.", "success");
      onClose();
    },
    onError: (err: AddMembersPartiesGroupGroupApiIdAddMembersPostError) => {
      console.log(err);
      const errDetail = err.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
    },
  });

  const onSubmit: SubmitHandler<AddMembersFormType> = async (data) => {
    const memberEmails = data.member_emails
      .split(",")
      .map((email) => email.trim());
    mutation.mutate({ member_emails: memberEmails });
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
