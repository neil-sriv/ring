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
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  CreateGroupPartiesGroupPostError,
  type GroupCreate,
  UserLinked,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import {
  createGroupPartiesGroupPostMutation,
  listGroupsPartiesGroupsGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

interface AddGroupProps {
  isOpen: boolean;
  onClose: () => void;
}

const AddGroup = ({ isOpen, onClose }: AddGroupProps) => {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);
  const showToast = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GroupCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
    },
  });

  const mutation = useMutation({
    ...createGroupPartiesGroupPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Group created successfully.", "success");
      reset();
      onClose();
    },
    onError: (err: AxiosError<CreateGroupPartiesGroupPostError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: (data) => {
      if (data) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser!.api_identifier },
          }),
        });
      }
    },
  });

  const onSubmit: SubmitHandler<GroupCreate> = (data) => {
    mutation.mutate({
      body: {
        admin_api_identifier: currentUser!.api_identifier,
        name: data.name,
      },
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
          <ModalHeader>Add Group</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isRequired isInvalid={!!errors.name}>
              <FormLabel htmlFor="name">Name</FormLabel>
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required.",
                })}
                placeholder="Name"
                type="text"
              />
              {errors.name && (
                <FormErrorMessage>{errors.name.message}</FormErrorMessage>
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

export default AddGroup;
