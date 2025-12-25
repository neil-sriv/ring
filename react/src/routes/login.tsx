import { ViewIcon, ViewOffIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  Center,
  Container,
  FormControl,
  FormErrorMessage,
  Heading,
  Icon,
  Input,
  InputGroup,
  InputRightElement,
  Link,
  Text,
  VStack,
  useBoolean,
  useColorModeValue,
} from "@chakra-ui/react";
import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router";
import { motion } from "framer-motion";
import { type SubmitHandler, useForm } from "react-hook-form";

import type { BodyLoginAccessTokenLoginAccessTokenPost as AccessToken } from "../client";
import useAuth from "../hooks/useAuth";
import { emailPattern } from "../util/misc";

const MotionBox = motion(Box);

export const Route = createFileRoute("/login")({
  component: Login,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      next: (search.next as string) || undefined,
    };
  },
  beforeLoad: async ({ context, search }) => {
    if (
      context.auth.isAuthenticated &&
      localStorage.getItem("access_token") !== null
    ) {
      // If already authenticated and there's a next parameter, redirect there
      // Otherwise redirect to home
      throw redirect({
        to: search.next || "/",
      });
    }
  },
});

function Login() {
  const [show, setShow] = useBoolean();
  const { data: search } = Route.useSearch();
  const { loginMutation, error, resetError } = useAuth(search.next);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const bgColor = useColorModeValue("rgba(255, 255, 255, 0.8)", "rgba(26, 32, 44, 0.8)");
  const borderColor = useColorModeValue("rgba(255, 255, 255, 0.2)", "rgba(255, 255, 255, 0.1)");
  const textColor = useColorModeValue("gray.800", "white");

  const onSubmit: SubmitHandler<AccessToken> = async (data) => {
    if (isSubmitting) return;

    resetError();

    try {
      await loginMutation.mutateAsync({
        body: data,
      });
    } catch {
      // error is handled by useAuth hook
    }
  };

  return (
    <Center
      minH="100vh"
      bgGradient="linear(to-br, ui.main, ui.darkSlate)"
      position="relative"
      overflow="hidden"
    >
      {/* Background animated circles */}
      <Box
        position="absolute"
        w="100%"
        h="100%"
        opacity={0.15}
        zIndex={0}
      >
        <MotionBox
          position="absolute"
          top="20%"
          left="10%"
          w="300px"
          h="300px"
          borderRadius="full"
          bg="ui.main"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.4, 0.6, 0.4],
            x: [0, 30, 0],
            y: [0, -20, 0],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <MotionBox
          position="absolute"
          bottom="20%"
          right="10%"
          w="400px"
          h="400px"
          borderRadius="full"
          bg="ui.darkSlate"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.6, 0.4, 0.6],
            x: [0, -40, 0],
            y: [0, 30, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <MotionBox
          position="absolute"
          top="50%"
          left="50%"
          w="200px"
          h="200px"
          borderRadius="full"
          bg="ui.main"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
            x: [-100, 100, -100],
            y: [-50, 50, -50],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </Box>

      <MotionBox
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        zIndex={1}
      >
        <Container
          as="form"
          onSubmit={handleSubmit(onSubmit)}
          maxW="sm"
          p={8}
          borderRadius="xl"
          bg={bgColor}
          backdropFilter="blur(10px)"
          border="1px solid"
          borderColor={borderColor}
          boxShadow="xl"
        >
          <VStack spacing={6} align="stretch">
            <Heading
              as="h1"
              size="xl"
              textAlign="center"
              color={textColor}
              fontWeight="bold"
              letterSpacing="tight"
            >
              Login
            </Heading>
            <Text textAlign="center" color="ui.dim" fontSize="sm">
              Enter your credentials
            </Text>

            <FormControl id="username" isInvalid={!!errors.username || !!error}>
              <Input
                id="username"
                {...register("username", {
                  pattern: emailPattern,
                })}
                placeholder="Email"
                type="email"
                required
                size="lg"
                bg="whiteAlpha.900"
                _hover={{ bg: "whiteAlpha.800" }}
                _focus={{ bg: "whiteAlpha.900" }}
                transition="all 0.2s"
              />
              {errors.username && (
                <FormErrorMessage>{errors.username.message}</FormErrorMessage>
              )}
            </FormControl>

            <FormControl id="password" isInvalid={!!error}>
              <InputGroup>
                <Input
                  {...register("password")}
                  type={show ? "text" : "password"}
                  placeholder="Password"
                  required
                  size="lg"
                  bg="whiteAlpha.900"
                  _hover={{ bg: "whiteAlpha.800" }}
                  _focus={{ bg: "whiteAlpha.900" }}
                  transition="all 0.2s"
                />
                <InputRightElement h="full">
                  <Icon
                    onClick={setShow.toggle}
                    aria-label={show ? "Hide password" : "Show password"}
                    cursor="pointer"
                    color="ui.dim"
                    _hover={{ color: "ui.main" }}
                    transition="color 0.2s"
                  >
                    {show ? <ViewOffIcon /> : <ViewIcon />}
                  </Icon>
                </InputRightElement>
              </InputGroup>
              {error && <FormErrorMessage>{error}</FormErrorMessage>}
            </FormControl>

            <Center>
              <Link
                as={RouterLink}
                to="/reset-password"
                color="ui.main"
                fontSize="sm"
                _hover={{ color: "ui.darkSlate", textDecoration: "none" }}
                transition="color 0.2s"
              >
                Forgot password?
              </Link>
            </Center>

            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
              size="lg"
              w="full"
              _hover={{
                transform: "translateY(-2px)",
                boxShadow: "lg",
              }}
              _active={{
                transform: "translateY(0)",
              }}
              transition="all 0.2s"
            >
              Sign In
            </Button>
          </VStack>
        </Container>
      </MotionBox>
    </Center>
  );
}
