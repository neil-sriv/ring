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
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import { useNavigate } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import type {
  ImpersonateUserTokenImpersonateUserTokenPostError,
  Token,
  UserLinked,
} from "../../client"
import {
  impersonateUserTokenImpersonateUserTokenPostMutation,
  readUserMePartiesMeGetOptions,
  readUsersPartiesUsersGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"

interface ImpersonateUserProps {
  user: UserLinked
  isOpen: boolean
  onClose: () => void
}

interface UserImpersonateForm {
  id: string
}

const ImpersonateUser = ({ user, isOpen, onClose }: ImpersonateUserProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserImpersonateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      id: user.api_identifier,
    },
  })

  const mutation = useMutation({
    ...impersonateUserTokenImpersonateUserTokenPostMutation(),
    onSuccess: (data: Token) => {
      showToast("Success!", "Impersonated user successfully.", "success")
      reset()
      onClose()
      localStorage.setItem("access_token", data.access_token)
      queryClient.invalidateQueries()
      queryClient.ensureQueryData({
        ...readUserMePartiesMeGetOptions({}),
      })
      navigate({ to: "/" })
    },
    onError: (
      err: AxiosError<ImpersonateUserTokenImpersonateUserTokenPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserImpersonateForm> = async () => {
    mutation.mutate({
      query: {
        user_api_id: user.api_identifier,
      },
    })
  }

  const onCancel = () => {
    reset()
    onClose()
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay />
        <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Impersonate User</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl>
              <FormLabel htmlFor="id">User ID</FormLabel>
              <Input
                id="id"
                {...register("id", {
                  required: "User ID is required",
                })}
                placeholder="User ID"
                type="text"
              />
              {errors.id && (
                <FormErrorMessage>{errors.id.message}</FormErrorMessage>
              )}
            </FormControl>
          </ModalBody>

          <ModalFooter gap={3}>
            <Button variant="primary" type="submit" isLoading={isSubmitting}>
              Save
            </Button>
            <Button onClick={onCancel}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default ImpersonateUser
