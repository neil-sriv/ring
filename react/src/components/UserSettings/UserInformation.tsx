import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  UpdateUserMePartiesMePatchError,
  UserLinked,
  UserUpdate,
} from "../../client"
import {
  readUserMePartiesMeGetQueryKey,
  readUsersPartiesUsersGetQueryKey,
  updateUserMePartiesMePatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { emailPattern } from "../../util/misc"
import { subscribeToPush } from "../../util/notifications"

const UserInformation = () => {
  const queryClient = useQueryClient()
  const textColor = useColorModeValue("ui.dark", "ui.light")
  const showToast = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<UserLinked>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: currentUser?.name,
      email: currentUser?.email,
    },
  })

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const mutation = useMutation({
    ...updateUserMePartiesMePatchMutation(),
    onSuccess: () => {
      showToast("Success!", "User updated successfully.", "success")
      reset()
    },
    onError: (err: AxiosError<UpdateUserMePartiesMePatchError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: async () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      })
      await queryClient.refetchQueries({
        queryKey: readUserMePartiesMeGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserUpdate> = async (data) => {
    mutation.mutate({ body: data })
  }

  const onCancel = () => {
    reset()
    toggleEditMode()
  }

  return (
    <Container maxW="full">
      <VStack spacing={6} align="stretch">
        <Heading size="sm" color={textColor}>
          User Information
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
            <FormControl>
              <FormLabel color={textColor} htmlFor="name">
                Full name
              </FormLabel>
              {editMode ? (
                <Input
                  id="name"
                  {...register("name", { maxLength: 30 })}
                  type="text"
                  size="md"
                  bg="whiteAlpha.900"
                  _hover={{ bg: "whiteAlpha.800" }}
                  _focus={{ bg: "whiteAlpha.900" }}
                  transition="all 0.2s"
                />
              ) : (
                <Text
                  size="md"
                  py={2}
                  color={!currentUser?.name ? "ui.dim" : textColor}
                >
                  {currentUser?.name || "N/A"}
                </Text>
              )}
            </FormControl>
            <FormControl isInvalid={!!errors.email}>
              <FormLabel color={textColor} htmlFor="email">
                Email
              </FormLabel>
              {editMode ? (
                <Input
                  id="email"
                  {...register("email", {
                    required: "Email is required",
                    pattern: emailPattern,
                  })}
                  type="email"
                  size="md"
                  bg="whiteAlpha.900"
                  _hover={{ bg: "whiteAlpha.800" }}
                  _focus={{ bg: "whiteAlpha.900" }}
                  transition="all 0.2s"
                />
              ) : (
                <Text size="md" py={2} color={textColor}>
                  {currentUser?.email}
                </Text>
              )}
              {errors.email && (
                <FormErrorMessage>{errors.email.message}</FormErrorMessage>
              )}
            </FormControl>
            <Flex gap={3}>
              <Button
                variant="primary"
                onClick={toggleEditMode}
                type={editMode ? "button" : "submit"}
                isLoading={editMode ? isSubmitting : false}
                isDisabled={editMode ? !isDirty || !getValues("email") : false}
              >
                {editMode ? "Save" : "Edit"}
              </Button>
              {editMode && (
                <Button onClick={onCancel} isDisabled={isSubmitting}>
                  Cancel
                </Button>
              )}
            </Flex>
          </VStack>
        </Box>
        <Box>
          <Button
            variant="glass"
            onClick={() => {
              subscribeToPush(currentUser!.api_identifier)
            }}
          >
            Enable Notifications
          </Button>
        </Box>
      </VStack>
    </Container>
  )
}

export default UserInformation
