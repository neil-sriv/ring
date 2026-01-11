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
  useColorModeValue,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  CreateGroupPartiesGroupPostError,
  GroupCreate,
  UserLinked,
} from "../../client"
import {
  createGroupPartiesGroupPostMutation,
  listGroupsPartiesGroupsGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"

interface AddGroupProps {
  isOpen: boolean
  onClose: () => void
}

const AddGroup = ({ isOpen, onClose }: AddGroupProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const showToast = useCustomToast()
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
  })

  const mutation = useMutation({
    ...createGroupPartiesGroupPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Group created successfully.", "success")
      reset()
      onClose()
    },
    onError: (err: AxiosError<CreateGroupPartiesGroupPostError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: (data) => {
      if (data) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser!.api_identifier },
          }),
        })
      }
    },
  })

  const onSubmit: SubmitHandler<GroupCreate> = (data) => {
    mutation.mutate({
      body: {
        admin_api_identifier: currentUser!.api_identifier,
        name: data.name,
      },
    })
  }

  const textColor = useColorModeValue("ui.dark", "ui.light")

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent
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
        >
          <ModalHeader color={textColor}>Add Group</ModalHeader>
          <ModalCloseButton color={textColor} />
          <ModalBody pb={6}>
            <FormControl isRequired isInvalid={!!errors.name}>
              <FormLabel htmlFor="name" color={textColor}>
                Name
              </FormLabel>
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required.",
                })}
                placeholder="Name"
                type="text"
                bg="ui.glass.light.background"
                borderColor="ui.glass.light.border"
                _dark={{
                  bg: "ui.glass.dark.background",
                  borderColor: "ui.glass.dark.border",
                }}
                _hover={{
                  borderColor: "ui.primary",
                }}
                _focus={{
                  borderColor: "ui.primary",
                  boxShadow: "0 0 0 1px var(--chakra-colors-ui-primary)",
                }}
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
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
              _hover={{
                opacity: 0.9,
                bg: "ui.primary",
              }}
              transition="all 0.2s ease-in-out"
            >
              Save
            </Button>
            <Button onClick={onClose} variant="glass">
              Cancel
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default AddGroup
