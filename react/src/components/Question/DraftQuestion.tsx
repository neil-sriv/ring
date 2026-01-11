import {
  Box,
  Button,
  Flex,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Textarea,
  useDisclosure,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useState } from "react"
import { FaTrash } from "react-icons/fa"
import {
  type DeleteQuestionQuestionsQuestionQuestionApiIdDeleteError,
  type PublicQuestion,
  type ResponseWithParticipant,
  type UserLinked,
  uploadImageQuestionsQuestionQuestionApiIdUploadImagePost,
  upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost,
} from "../../client"
import {
  deleteQuestionQuestionsQuestionQuestionApiIdDeleteMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import {
  S3Image,
  S3Video,
  SingleUploadImage,
} from "../Common/SingleUploadImage"

type ResponseBlockProps = {
  uploadFunction: (file: File) => Promise<void>
  questionApiId: string
  response?: ResponseWithParticipant
  submitResponse: (responseText: string) => Promise<void>
  readOnly?: boolean
}

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(
    props.response?.response_text ?? "",
  )
  const showToast = useCustomToast()
  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResponseText(e.target.value)
  }

  return (
    <Box my="10px">
      <Textarea
        size="md"
        variant="filled"
        value={responseText}
        onChange={handleResponseChange}
        isDisabled={props.readOnly}
        onBlur={async () => {
          if ((props.response?.response_text ?? "") !== responseText) {
            await props.submitResponse(responseText)
            showToast("Success!", "Answer saved.", "success")
          }
        }}
      />
      {props.response?.images.map((image, index) => {
        return image.media_type === "image" ? (
          <S3Image s3Key={image.s3_url} alt="response" key={index} />
        ) : (
          <S3Video s3Key={image.s3_url} key={index} />
        )
      })}
      {!props.readOnly && (
        <SingleUploadImage
          onUpdateFile={props.uploadFunction}
          name={props.questionApiId}
        />
      )}
    </Box>
  )
}

function DraftQuestion({
  question,
  loopApiId,
  readOnly = false,
  isGroupAdmin = false,
}: {
  question: PublicQuestion
  loopApiId: string
  readOnly?: boolean
  isGroupAdmin?: boolean
}): JSX.Element {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const showToast = useCustomToast()
  const deleteModal = useDisclosure()

  if (!currentUser) {
    return <Box>loading...</Box>
  }
  const response = question.responses.find(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier,
  )

  const isAuthor =
    question.author?.api_identifier === currentUser.api_identifier
  const canDelete = isAuthor || isGroupAdmin

  const deleteMutation = useMutation({
    ...deleteQuestionQuestionsQuestionQuestionApiIdDeleteMutation(),
    onSuccess: () => {
      showToast("Success!", "Question deleted successfully.", "success")
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      })
    },
    onError: (
      error: AxiosError<DeleteQuestionQuestionsQuestionQuestionApiIdDeleteError>,
    ) => {
      const errDetail =
        error.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
  })

  const handleDelete = async () => {
    await deleteMutation.mutateAsync({
      path: { question_api_id: question.api_identifier },
    })
    deleteModal.onClose()
  }

  const handleUpsert = async (responseText: string) => {
    await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_text: responseText,
        participant_api_identifier: currentUser.api_identifier,
      },
    })
  }

  const newHandleUpload = async (file: File) => {
    await uploadImageQuestionsQuestionQuestionApiIdUploadImagePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_image: file,
      },
    })
    queryClient.invalidateQueries({
      queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
        path: { letter_api_id: loopApiId },
      }),
    })
  }

  return (
    <Box my="20px">
      <Flex justify="space-between" align="center">
        {question.author == null ? (
          <Heading size="md">{question.question_text}</Heading>
        ) : (
          <Heading size="md">
            {question.author.name} asked: {question.question_text}
          </Heading>
        )}
        {canDelete && readOnly && (
          <Button
            variant="ghost"
            colorScheme="red"
            size="sm"
            onClick={deleteModal.onOpen}
            leftIcon={<FaTrash />}
          >
            Delete
          </Button>
        )}
      </Flex>
      <ResponseBlock
        questionApiId={question.api_identifier}
        response={response}
        submitResponse={handleUpsert}
        uploadFunction={newHandleUpload}
        key={question.api_identifier}
        readOnly={readOnly}
      />

      <Modal isOpen={deleteModal.isOpen} onClose={deleteModal.onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete Question</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            Are you sure you want to delete this question? This action cannot be
            undone.
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={deleteModal.onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="red"
              onClick={handleDelete}
              isLoading={deleteMutation.isPending}
            >
              Delete
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default DraftQuestion
