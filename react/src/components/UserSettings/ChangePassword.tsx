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
    VStack,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import { AxiosError } from "axios";
import {
    type UserUpdatePassword,
    UpdatePasswordMePartiesMePasswordPatchError,
} from "../../client";
import { updatePasswordMePartiesMePasswordPatchMutation } from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";
import { confirmPasswordRules, passwordRules } from "../../util/misc";

interface UpdatePasswordForm extends UserUpdatePassword {
  confirm_password: string;
}

const ChangePassword = () => {
  const textColor = useColorModeValue("ui.dark", "ui.light");
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
    ...updatePasswordMePartiesMePasswordPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "Password updated.", "success");
      reset();
    },
    onError: (err: AxiosError<UpdatePasswordMePartiesMePasswordPatchError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
  });

  const onSubmit: SubmitHandler<UpdatePasswordForm> = async (data) => {
    mutation.mutate({
      body: data,
    });
  };

  return (
    <Container maxW="full">
      <VStack spacing={6} align="stretch">
        <Heading size="sm" color={textColor}>
          Change Password
        </Heading>
        <Box
          w={{ sm: "full", md: "50%" }}
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
          p={6}
          borderRadius="xl"
          boxShadow="md"
        >
          <VStack spacing={4} align="stretch">
            <FormControl isRequired isInvalid={!!errors.current_password}>
              <FormLabel color={textColor} htmlFor="current_password">
                Current Password
              </FormLabel>
              <Input
                id="current_password"
                {...register("current_password")}
                placeholder="Password"
                type="password"
                bg="whiteAlpha.900"
                _hover={{ bg: "whiteAlpha.800" }}
                _focus={{ bg: "whiteAlpha.900" }}
                transition="all 0.2s"
              />
              {errors.current_password && (
                <FormErrorMessage>
                  {errors.current_password.message}
                </FormErrorMessage>
              )}
            </FormControl>
            <FormControl isRequired isInvalid={!!errors.new_password}>
              <FormLabel color={textColor} htmlFor="password">
                Set Password
              </FormLabel>
              <Input
                id="password"
                {...register("new_password", passwordRules())}
                placeholder="Password"
                type="password"
                bg="whiteAlpha.900"
                _hover={{ bg: "whiteAlpha.800" }}
                _focus={{ bg: "whiteAlpha.900" }}
                transition="all 0.2s"
              />
              {errors.new_password && (
                <FormErrorMessage>{errors.new_password.message}</FormErrorMessage>
              )}
            </FormControl>
            <FormControl isRequired isInvalid={!!errors.confirm_password}>
              <FormLabel color={textColor} htmlFor="confirm_password">
                Confirm Password
              </FormLabel>
              <Input
                id="confirm_password"
                {...register("confirm_password", confirmPasswordRules(getValues))}
                placeholder="Password"
                type="password"
                bg="whiteAlpha.900"
                _hover={{ bg: "whiteAlpha.800" }}
                _focus={{ bg: "whiteAlpha.900" }}
                transition="all 0.2s"
              />
              {errors.confirm_password && (
                <FormErrorMessage>
                  {errors.confirm_password.message}
                </FormErrorMessage>
              )}
            </FormControl>
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
            >
              Save
            </Button>
          </VStack>
        </Box>
      </VStack>
    </Container>
  );
};

export default ChangePassword;
