import {
  Button,
  FormControl,
  FormErrorMessage,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Textarea,
  useColorModeValue,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"

import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { useState } from "react"
import type {
  AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
  UserLinked,
} from "../../client"
import {
  addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
  generateQuestionLettersLetterLetterApiIdGenerateQuestionPostMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"

type QuestionFormProps = {
  questionPrompt: string
}

interface GenerateQuestionProps {
  isOpen: boolean
  onClose: () => void
  loopApiId: string
}

const GenerateQuestion = ({
  isOpen,
  onClose,
  loopApiId,
}: GenerateQuestionProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const router = useRouter()
  const showToast = useCustomToast()
  const [generatedQuestion, setGeneratedQuestion] = useState<string>("")
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<QuestionFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
  })
  const textColor = useColorModeValue("ui.dark", "ui.light")

  const generateQuestionMutation = useMutation({
    ...generateQuestionLettersLetterLetterApiIdGenerateQuestionPostMutation({
      path: { letter_api_id: loopApiId },
    }),
    onSuccess: (data) => {
      setGeneratedQuestion(data.generated_text)
      showToast("Success!", "Question generated successfully.", "success")
    },
    onError: (
      err: AxiosError<AddQuestionLettersLetterLetterApiIdAddQuestionPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
  })

  const addQuestionMutation = useMutation({
    ...addQuestionLettersLetterLetterApiIdAddQuestionPostMutation(),
    onSuccess: () => {
      showToast("Success!", "New question created successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      err: AxiosError<AddQuestionLettersLetterLetterApiIdAddQuestionPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      })
      router.invalidate()
    },
  })

  const onGenerateQuestion: SubmitHandler<QuestionFormProps> = (data) => {
    generateQuestionMutation.mutate({
      body: {
        prompt: data.questionPrompt,
      },
      path: { letter_api_id: loopApiId },
    })
  }

  const onSaveQuestion = () => {
    if (!generatedQuestion) {
      showToast(
        "Error",
        "No question to save. Please generate a question first.",
        "error",
      )
      return
    }

    addQuestionMutation.mutate({
      body: {
        question_text: generatedQuestion,
        author_api_id: currentUser?.api_identifier || null,
      },
      path: { letter_api_id: loopApiId },
    })
  }

  const handleClose = () => {
    reset()
    setGeneratedQuestion("")
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      size={{ base: "sm", md: "md" }}
      isCentered
    >
      <ModalOverlay backdropFilter="blur(4px)" />
      <ModalContent
        as="form"
        onSubmit={handleSubmit(onGenerateQuestion)}
        bg="ui.glass.light.background"
        backdropFilter="blur(10px)"
        border="1px solid"
        borderColor="ui.glass.light.border"
        _dark={{
          bg: "ui.glass.dark.background",
          borderColor: "ui.glass.dark.border",
        }}
      >
        <ModalHeader color={textColor}>Generate question</ModalHeader>
        <ModalCloseButton color={textColor} />
        <ModalBody pb={6}>
          <FormControl isInvalid={!!errors.questionPrompt}>
            <Textarea
              id="questionPrompt"
              placeholder="Enter a prompt to generate a question..."
              {...register("questionPrompt", {
                required: "Question prompt is required.",
              })}
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
              minH="100px"
            />
            {errors.questionPrompt && (
              <FormErrorMessage>
                {errors.questionPrompt.message}
              </FormErrorMessage>
            )}
          </FormControl>
          {generatedQuestion && (
            <FormControl mt={4}>
              <Textarea
                id="generatedQuestion"
                value={generatedQuestion}
                readOnly
                placeholder="Generated question will appear here..."
                minH="100px"
                bg="ui.glass.light.background"
                borderColor="ui.glass.light.border"
                _dark={{
                  bg: "ui.glass.dark.background",
                  borderColor: "ui.glass.dark.border",
                }}
              />
            </FormControl>
          )}
        </ModalBody>

        <ModalFooter gap={3}>
          <Button
            variant="primary"
            type="submit"
            isLoading={generateQuestionMutation.isPending}
            _hover={{
              opacity: 0.9,
              bg: "ui.primary",
            }}
            transition="all 0.2s ease-in-out"
          >
            Generate
          </Button>
          <Button
            onClick={onSaveQuestion}
            isLoading={addQuestionMutation.isPending}
            isDisabled={!generatedQuestion}
            variant="glass"
          >
            Save
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

export default GenerateQuestion
