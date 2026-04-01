import {
  Button,
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
  Switch,
  Text,
  useColorModeValue,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  EditLetterLettersLetterLetterApiIdEditLetterPostError,
  LetterStatus,
  PublicLetter,
} from "../../client"
import {
  editLetterLettersLetterLetterApiIdEditLetterPostMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { toISOLocal } from "../../util/misc"

type LetterFormProps = {
  sendAt: Date | string
  title: string
  isInProgress: boolean
}

interface EditLetterProps {
  isOpen: boolean
  onClose: () => void
  loop: PublicLetter
}

const EditLetter = ({ isOpen, onClose, loop }: EditLetterProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const previousSendAt = new Date(loop.send_at)
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    values: isOpen
      ? {
          sendAt: toISOLocal(new Date(loop.send_at)).slice(0, 16),
          title: loop.title || "",
          isInProgress: loop.status === "IN_PROGRESS",
        }
      : undefined,
  })

  const mutation = useMutation({
    ...editLetterLettersLetterLetterApiIdEditLetterPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Letter updated successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      err: AxiosError<EditLetterLettersLetterLetterApiIdEditLetterPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
      })
    },
  })

  const onSubmit: SubmitHandler<LetterFormProps> = (data) => {
    const updateData: {
      send_at?: string
      title?: string
      status?: LetterStatus
    } = {}

    // Only include fields that have changed
    if (
      data.sendAt instanceof Date
        ? toISOLocal(data.sendAt)
        : data.sendAt !== toISOLocal(previousSendAt).slice(0, 16)
    ) {
      updateData.send_at =
        data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt
    }

    if (data.title !== (loop.title || "")) {
      updateData.title = data.title || undefined
    }

    const newStatus = data.isInProgress ? "IN_PROGRESS" : "UPCOMING"
    if (newStatus !== loop.status) {
      updateData.status = newStatus
    }

    // Only submit if there are changes
    if (Object.keys(updateData).length > 0) {
      mutation.mutate({
        body: updateData,
        path: { letter_api_id: loop.api_identifier },
      })
    } else {
      showToast("No changes", "No changes were made to the letter.", "success")
      onClose()
    }
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
          <ModalHeader color={textColor}>Edit Loop</ModalHeader>
          <ModalCloseButton color={textColor} />
          <ModalBody pb={6}>
            <FormControl mb={4}>
              <FormLabel htmlFor="title" color={textColor}>
                Title
              </FormLabel>
              <Input
                id="title"
                {...register("title")}
                placeholder="Enter letter title"
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
            </FormControl>

            <FormControl mb={4}>
              <FormLabel htmlFor="isInProgress" color={textColor}>
                Status
              </FormLabel>
              <Flex align="center" gap={4}>
                <Text
                  color={textColor}
                  fontSize="sm"
                  fontWeight={!watch("isInProgress") ? "bold" : "normal"}
                  opacity={!watch("isInProgress") ? 1 : 0.6}
                >
                  Upcoming
                </Text>
                <Switch
                  id="isInProgress"
                  {...register("isInProgress")}
                  colorScheme="teal"
                  size="lg"
                />
                <Text
                  color={textColor}
                  fontSize="sm"
                  fontWeight={watch("isInProgress") ? "bold" : "normal"}
                  opacity={watch("isInProgress") ? 1 : 0.6}
                >
                  In Progress
                </Text>
              </Flex>
            </FormControl>

            <FormControl isRequired>
              <FormLabel htmlFor="sendAt" color={textColor}>
                Send at
              </FormLabel>
              <Input
                id="sendAt"
                {...register("sendAt", {
                  required: "Send at is required.",
                  valueAsDate: true,
                })}
                type="datetime-local"
                min={toISOLocal(new Date()).slice(0, 16)}
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
              {errors.sendAt && (
                <FormErrorMessage>{errors.sendAt.message}</FormErrorMessage>
              )}
            </FormControl>
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

export default EditLetter
