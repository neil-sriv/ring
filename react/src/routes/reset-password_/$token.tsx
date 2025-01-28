import {
  Button,
  Container,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  Text,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  ResetPasswordResetPasswordTokenPostError,
  type NewPassword,
} from "../../client";
import { isLoggedIn } from "../../hooks/useAuth";
import useCustomToast from "../../hooks/useCustomToast";
import { confirmPasswordRules, passwordRules } from "../../util/misc";
import { resetPasswordResetPasswordTokenPostMutation } from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

interface NewPasswordForm extends NewPassword {
  confirm_password: string;
}

export const Route = createFileRoute("/reset-password/$token")({
  component: ResetPassword,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      });
    }
  },
});

function ResetPassword() {
  const {
    register,
    handleSubmit,
    getValues,
    reset,
    formState: { errors },
  } = useForm<NewPasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      new_password: "",
    },
  });
  const showToast = useCustomToast();
  const navigate = useNavigate();
  const { token } = Route.useParams();

  const mutation = useMutation({
    ...resetPasswordResetPasswordTokenPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Password updated.", "success");
      reset();
      navigate({ to: "/login" });
    },
    onError: (err: AxiosError<ResetPasswordResetPasswordTokenPostError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
  });

  const onSubmit: SubmitHandler<NewPasswordForm> = async (data) => {
    if (!token) return;
    mutation.mutate({
      path: { token: token },
      body: data,
    });
  };

  return (
    <Container
      as="form"
      onSubmit={handleSubmit(onSubmit)}
      h="100vh"
      maxW="sm"
      alignItems="stretch"
      justifyContent="center"
      gap={4}
      centerContent
    >
      <Heading size="xl" color="ui.main" textAlign="center" mb={2}>
        Reset Password
      </Heading>
      <Text textAlign="center">
        Please enter your new password and confirm it to reset your password.
      </Text>
      <FormControl mt={4} isInvalid={!!errors.new_password}>
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
      <FormControl mt={4} isInvalid={!!errors.confirm_password}>
        <FormLabel htmlFor="confirm_password">Confirm Password</FormLabel>
        <Input
          id="confirm_password"
          {...register("confirm_password", confirmPasswordRules(getValues))}
          placeholder="Password"
          type="password"
        />
        {errors.confirm_password && (
          <FormErrorMessage>{errors.confirm_password.message}</FormErrorMessage>
        )}
      </FormControl>
      <Button variant="primary" type="submit">
        Reset Password
      </Button>
    </Container>
  );
}
