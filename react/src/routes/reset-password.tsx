import {
  Button,
  Container,
  FormControl,
  FormErrorMessage,
  Heading,
  Input,
  Text,
} from "@chakra-ui/react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { type SubmitHandler, useForm } from "react-hook-form";

import { ApiError, LoginService } from "../client";
import { isLoggedIn } from "../hooks/useAuth";
import useCustomToast from "../hooks/useCustomToast";
import { emailPattern } from "../util/misc";

interface FormData {
  email: string;
}

export const Route = createFileRoute("/reset-password")({
  component: ResetPasswordRequest,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      });
    }
  },
});

function ResetPasswordRequest() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>();
  const showToast = useCustomToast();

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    await LoginService.resetPasswordRequestResetPasswordRequestEmailPost({
      email: data.email,
    })
      .then(() => {
        showToast(
          "Email sent.",
          "We sent an email with a link to get back into your account.",
          "success"
        );
      })
      .catch((error) => {
        showToast(
          "Something went wrong",
          (error as ApiError).body.detail,
          "error"
        );
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
        Password Reset
      </Heading>
      <Text align="center">
        A password reset email will be sent to the registered account.
      </Text>
      <FormControl isInvalid={!!errors.email}>
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
      <Button variant="primary" type="submit" isLoading={isSubmitting}>
        Continue
      </Button>
    </Container>
  );
}
