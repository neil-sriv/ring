import { ViewIcon, ViewOffIcon } from "@chakra-ui/icons";
import {
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
  useBoolean,
} from "@chakra-ui/react";
import {
  createFileRoute,
  redirect,
  Link as RouterLink,
} from "@tanstack/react-router";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  validateTokenInvitesTokenTokenGet,
  type UserCreate,
} from "../../client";
import { isLoggedIn } from "../../hooks/useAuth";
import { emailPattern } from "../../util/misc";
import useRegister from "../../hooks/useRegister";
import { useQueryClient } from "@tanstack/react-query";

export const Route = createFileRoute("/register/$token")({
  component: Register,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/groups",
      });
    }
  },
  loader: async ({ params, context }) => {
    await context.queryClient
      .ensureQueryData({
        queryKey: ["token", params.token],
        queryFn: async () => {
          return await validateTokenInvitesTokenTokenGet({
            path: { token: params.token },
          });
        },
      })
      .catch(() => {
        console.log("Invalid token");
      });
  },
});

function Register() {
  const { token } = Route.useParams();
  const queryClient = useQueryClient();
  const validToken =
    queryClient.getQueryData(["token", token]) ?? false ? true : false;
  if (!validToken) {
    return (
      <Center h="100vh">
        <Heading as="h1">Invalid token</Heading>
      </Center>
    );
  }

  const [show, setShow] = useBoolean();
  const { registerMutation, error, resetError } = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      name: "",
      password: "",
    },
  });

  const onSubmit: SubmitHandler<UserCreate> = async (data) => {
    if (isSubmitting) return;

    resetError();

    const formData = {
      body: data,
      path: { token: token },
    };

    try {
      console.log(formData);
      await registerMutation.mutateAsync(formData);
    } catch {
      // error is handled by useAuth hook
    }
  };

  return (
    <>
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
        {/* <Image
          src={Logo}
          alt="Ring logo"
          height="auto"
          maxW="2xs"
          alignSelf="center"
          mb={4}
        /> */}
        <Heading as="h1" size="lg" textAlign="center">
          Ring
        </Heading>
        <FormControl id="name" isInvalid={!!errors.name}>
          <Input
            {...register("name")}
            placeholder="Name"
            type="text"
            required
          />
          {errors.name && (
            <FormErrorMessage>{errors.name.message}</FormErrorMessage>
          )}
        </FormControl>
        <FormControl id="email" isInvalid={!!errors.email || !!error}>
          <Input
            id="email"
            {...register("email", {
              pattern: emailPattern,
            })}
            placeholder="Email"
            type="email"
            required
          />
          {errors.email && (
            <FormErrorMessage>{errors.email.message}</FormErrorMessage>
          )}
        </FormControl>
        <FormControl id="password" isInvalid={!!error}>
          <InputGroup>
            <Input
              {...register("password")}
              type={show ? "text" : "password"}
              placeholder="Password"
              required
            />
            <InputRightElement
              color="ui.dim"
              _hover={{
                cursor: "pointer",
              }}
            >
              <Icon
                onClick={setShow.toggle}
                aria-label={show ? "Hide password" : "Show password"}
              >
                {show ? <ViewOffIcon /> : <ViewIcon />}
              </Icon>
            </InputRightElement>
          </InputGroup>
          {error && <FormErrorMessage>{error}</FormErrorMessage>}
        </FormControl>
        <Center>
          <Link as={RouterLink} to="/login" color="blue.500">
            Already have an account?
          </Link>
        </Center>
        <Button variant="primary" type="submit" isLoading={isSubmitting}>
          Register
        </Button>
      </Container>
    </>
  );
}
