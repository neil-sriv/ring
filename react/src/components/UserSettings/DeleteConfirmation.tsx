import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Button,
  useColorModeValue,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import React from "react"
import { useForm } from "react-hook-form"

import { deleteUserPartiesUserIdDelete } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import useCustomToast from "../../hooks/useCustomToast"

interface DeleteProps {
  isOpen: boolean
  onClose: () => void
}

const DeleteConfirmation = ({ isOpen, onClose }: DeleteProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const cancelRef = React.useRef<HTMLButtonElement | null>(null)
  const textColor = useColorModeValue("ui.dark", "ui.light")
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()
  const { logout } = useAuth()

  const mutation = useMutation({
    mutationFn: () => deleteUserPartiesUserIdDelete(),
    onSuccess: () => {
      showToast(
        "Success",
        "Your account has been successfully deleted.",
        "success",
      )
      logout()
      queryClient.clear()
      onClose()
    },
    onError: (err: Error) => {
      const errDetail = err.message || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readUserMePartiesMeGetQueryKey(),
      })
    },
  })

  const onSubmit = async () => {
    mutation.mutate()
  }

  return (
    <AlertDialog
      isOpen={isOpen}
      onClose={onClose}
      leastDestructiveRef={cancelRef}
      size={{ base: "sm", md: "md" }}
      isCentered
    >
      <AlertDialogOverlay backdropFilter="blur(4px)" />
      <AlertDialogContent
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
        <AlertDialogHeader color={textColor}>
          Confirmation Required
        </AlertDialogHeader>

        <AlertDialogBody color={textColor}>
          All your account data will be <strong>permanently deleted.</strong> If
          you are sure, please click <strong>"Confirm"</strong> to proceed. This
          action cannot be undone.
        </AlertDialogBody>

        <AlertDialogFooter gap={3}>
          <Button
            variant="danger"
            type="submit"
            isLoading={isSubmitting}
            _hover={{ transform: "translateY(-2px)" }}
            transition="all 0.2s"
          >
            Confirm
          </Button>
          <Button
            ref={cancelRef}
            onClick={onClose}
            isDisabled={isSubmitting}
            variant="glass"
          >
            Cancel
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default DeleteConfirmation
