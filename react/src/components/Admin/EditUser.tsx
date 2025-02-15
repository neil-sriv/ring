import {
  Button,
  // Checkbox,
  Flex,
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

import { type UserLinked, UserUpdate } from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { emailPattern } from "../../util/misc";
import {
  readUsersPartiesUsersGetQueryKey,
  updateUserPartiesUserIdPatchMutation,
} from "../../client/@tanstack/react-query.gen";

interface EditUserProps {
  user: UserLinked;
  isOpen: boolean;
  onClose: () => void;
}

interface UserUpdateForm extends UserUpdate {
  confirm_password: string;
}

const EditUser = ({ user, isOpen, onClose }: EditUserProps) => {
  const queryClient = useQueryClient();
  const showToast = useCustomToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<UserUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: user,
  });

  const mutation = useMutation({
    ...updateUserPartiesUserIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "User updated successfully.", "success");
      reset();
      onClose();
    },
    // onError: (err: AxiosError<UpdateUserMePartiesMePatchError>) => {
    //   const errDetail =
    //     err.response?.data.detail || "no error detail, please contact support";
    //   showToast("Something went wrong.", `${errDetail}`, "error");
    // },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      });
    },
  });

  const onSubmit: SubmitHandler<UserUpdateForm> = async () => {
    mutation.mutate({});
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
          <ModalHeader>Edit User</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isInvalid={!!errors.email}>
              <FormLabel htmlFor="email">Email</FormLabel>
              <Input
                id="email"
                {...register("email", {
                  required: "Email is required",
                  pattern: emailPattern,
                })}
                placeholder="Email"
                type="email"
              />
              {errors.email && (
                <FormErrorMessage>{errors.email.message}</FormErrorMessage>
              )}
            </FormControl>
            <FormControl mt={4}>
              <FormLabel htmlFor="name">Full name</FormLabel>
              <Input id="name" {...register("name")} type="text" />
            </FormControl>
            {/* <FormControl mt={4} isInvalid={!!errors.password}>
              <FormLabel htmlFor="password">Set Password</FormLabel>
              <Input
                id="password"
                {...register("password", {
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                })}
                placeholder="Password"
                type="password"
              />
              {errors.password && (
                <FormErrorMessage>{errors.password.message}</FormErrorMessage>
              )}
            </FormControl> */}
            {/* <FormControl mt={4} isInvalid={!!errors.confirm_password}>
              <FormLabel htmlFor="confirm_password">Confirm Password</FormLabel>
              <Input
                id="confirm_password"
                {...register("confirm_password", {
                  validate: (value) =>
                    value === getValues().password ||
                    "The passwords do not match",
                })}
                placeholder="Password"
                type="password"
              />
              {errors.confirm_password && (
                <FormErrorMessage>
                  {errors.confirm_password.message}
                </FormErrorMessage>
              )}
            </FormControl> */}
            <Flex>
              <FormControl mt={4}>
                {/* <Checkbox {...register("is_superuser")} colorScheme="teal">
                  Is superuser?
                </Checkbox> */}
              </FormControl>
              <FormControl mt={4}>
                {/* <Checkbox {...register("is_active")} colorScheme="teal">
                  Is active?
                </Checkbox> */}
              </FormControl>
            </Flex>
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

export default EditUser;
