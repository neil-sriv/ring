import {
  Box,
  Button,
  Container,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  useColorModeValue,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  type UserUpdatePassword,
  updatePasswordMePartiesMePasswordPatch,
  UpdatePasswordMePartiesMePasswordPatchError,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { confirmPasswordRules, passwordRules } from "../../util/misc";

interface UpdatePasswordForm extends UserUpdatePassword {
  confirm_password: string;
}

const ChangePassword = () => {
  const color = useColorModeValue("inherit", "ui.light");
  const showToast = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UpdatePasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
  });

  const mutation = useMutation({
    mutationFn: (data: UpdatePasswordForm) =>
      updatePasswordMePartiesMePasswordPatch({
        body: {
          current_password: data.current_password,
          new_password: data.new_password,
        },
      }),
    onSuccess: () => {
      showToast("Success!", "Password updated.", "success");
      reset();
    },
    onError: (err: UpdatePasswordMePartiesMePasswordPatchError) => {
      const errDetail = err.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
  });

  const onSubmit: SubmitHandler<UpdatePasswordForm> = async (data) => {
    mutation.mutate(data);
  };

  return (
    <>
      <Container maxW="full">
        <Heading size="sm" py={4}>
          Change Password
        </Heading>
        <Box
          w={{ sm: "full", md: "50%" }}
          as="form"
          onSubmit={handleSubmit(onSubmit)}
        >
          <FormControl isRequired isInvalid={!!errors.current_password}>
            <FormLabel color={color} htmlFor="current_password">
              Current Password
            </FormLabel>
            <Input
              id="current_password"
              {...register("current_password")}
              placeholder="Password"
              type="password"
            />
            {errors.current_password && (
              <FormErrorMessage>
                {errors.current_password.message}
              </FormErrorMessage>
            )}
          </FormControl>
          <FormControl mt={4} isRequired isInvalid={!!errors.new_password}>
            <FormLabel htmlFor="password">Set Password</FormLabel>
            <Input
              id="password"
              {...register("new_password", passwordRules())}
              placeholder="Password"
              type="password"
            />
            {errors.new_password && (
              <FormErrorMessage>{errors.new_password.message}</FormErrorMessage>
            )}
          </FormControl>
          <FormControl mt={4} isRequired isInvalid={!!errors.confirm_password}>
            <FormLabel htmlFor="confirm_password">Confirm Password</FormLabel>
            <Input
              id="confirm_password"
              {...register("confirm_password", confirmPasswordRules(getValues))}
              placeholder="Password"
              type="password"
            />
            {errors.confirm_password && (
              <FormErrorMessage>
                {errors.confirm_password.message}
              </FormErrorMessage>
            )}
          </FormControl>
          <Button
            variant="primary"
            mt={4}
            type="submit"
            isLoading={isSubmitting}
          >
            Save
          </Button>
        </Box>
      </Container>
    </>
  );
};
export default ChangePassword;
