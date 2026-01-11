import {
  Box,
  Button,
  Heading,
  Textarea,
  useColorModeValue,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useState } from "react"
import {
  type PublicQuestion,
  type UpsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePostError,
  type UserLinked,
  upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost,
} from "../../client"
import {
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"

interface LateAnswerQuestionProps {
  question: PublicQuestion
  loopApiId: string
}

function LateAnswerQuestion({
  question,
  loopApiId,
}: LateAnswerQuestionProps): JSX.Element {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const showToast = useCustomToast()
  const [responseText, setResponseText] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!currentUser) {
    return <Box>Loading...</Box>
  }

  // Check if user has already responded to this question
  const hasResponded = question.responses.some(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier,
  )

  // If user has already responded, don't show the late answer form
  if (hasResponded) {
    return <></>
  }

  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResponseText(e.target.value)
  }

  const mutation = useMutation({
    mutationFn: async () => {
      await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
        path: { question_api_id: question.api_identifier },
        body: {
          response_text: responseText,
          participant_api_identifier: currentUser.api_identifier,
        },
      })
    },
    onSuccess: () => {
      showToast("Success!", "Your late answer has been submitted.", "success")
      setResponseText("")
      // Invalidate the letter query to refresh the data
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      })
    },
    onError: (
      err: AxiosError<UpsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePostError>,
    ) => {
      const errDetail =
        err.response?.data.detail ||
        "Failed to submit late answer. Please try again."
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      setIsSubmitting(false)
    },
  })

  const handleSubmit = async () => {
    if (!responseText.trim()) {
      showToast("Error", "Please enter your answer before submitting.", "error")
      return
    }
    setIsSubmitting(true)
    mutation.mutate()
  }

  const textColor = useColorModeValue("ui.dark", "ui.light")

  return (
    <Box
      my="20px"
      p="4"
      border="1px"
      borderColor="gray.200"
      borderRadius="md"
      bg="gray.50"
      _dark={{
        borderColor: "gray.600",
        bg: "gray.700",
      }}
    >
      <Heading size="md" mb="3" color={textColor}>
        {question.author == null ? (
          question.question_text
        ) : (
          <>
            {question.author.name} asked: {question.question_text}
          </>
        )}
      </Heading>

      <Box mb="3">
        <Textarea
          size="md"
          variant="filled"
          value={responseText}
          onChange={handleResponseChange}
          placeholder="Add your late answer here..."
          minH="100px"
        />
      </Box>

      <Button
        colorScheme="blue"
        onClick={handleSubmit}
        isLoading={isSubmitting}
        loadingText="Submitting..."
        isDisabled={!responseText.trim()}
      >
        Submit Late Answer
      </Button>
    </Box>
  )
}

export default LateAnswerQuestion
