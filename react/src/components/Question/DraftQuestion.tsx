import { Box, Button, Flex, Heading, Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay, Textarea, useDisclosure } from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useEffect, useRef, useState } from "react";
import { FaTrash } from "react-icons/fa";
import {
  deleteImageResponsesResponseResponseApiIdDeleteImageDelete,
  DeleteQuestionQuestionsQuestionQuestionApiIdDeleteError,
  PublicQuestion,
  ResponseWithParticipant,
  uploadImageQuestionsQuestionQuestionApiIdUploadImagePost,
  upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost,
  UserLinked,
} from "../../client";
import {
  deleteQuestionQuestionsQuestionQuestionApiIdDeleteMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen";
import useCustomToast from "../../hooks/useCustomToast";
import {
  S3Image,
  S3Video,
  SingleUploadImage,
} from "../Common/SingleUploadImage";

type ResponseBlockProps = {
  uploadFunction: (file: File) => Promise<void>;
  deleteImage: (s3Url: string) => Promise<void>;
  questionApiId: string;
  response?: ResponseWithParticipant;
  submitResponse: (responseText: string) => Promise<void>;
  readOnly?: boolean;
};

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(
    props.response?.response_text ?? ""
  );
  const [isSaving, setIsSaving] = useState(false);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const savingStartTimeRef = useRef<number | null>(null);
  const showToast = useCustomToast();

  // Update local state when response prop changes
  useEffect(() => {
    setResponseText(props.response?.response_text ?? "");
  }, [props.response?.response_text]);

  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setResponseText(newValue);

    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set new timeout for debounced save
    debounceTimeoutRef.current = setTimeout(async () => {
      if (newValue !== (props.response?.response_text ?? "")) {
        savingStartTimeRef.current = Date.now();
        setIsSaving(true);
        try {
          await props.submitResponse(newValue);
          showToast("Success!", "Answer saved.", "success");
        } catch (error) {
          console.error("Failed to save response:", error);
          showToast("Error!", "Failed to save answer.", "error");
        } finally {
          // Ensure saving animation shows for at least 250ms
          const elapsed = Date.now() - (savingStartTimeRef.current || 0);
          const remainingTime = Math.max(0, 250 - elapsed);

          setTimeout(() => {
            setIsSaving(false);
          }, remainingTime);
        }
      }
    }, 1000); // 1 second debounce
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  return (
    <Box my="10px">
      <Textarea
        size="md"
        variant="filled"
        value={responseText}
        onChange={handleResponseChange}
        isDisabled={props.readOnly}
        placeholder={isSaving ? "Saving..." : "Type your response..."}
        opacity={isSaving ? 0.7 : 1}
        transition="opacity 0.2s ease"
      />
      {isSaving && (
        <Box fontSize="sm" color="gray.500" mt={1}>
          Saving...
        </Box>
      )}
      {!props.readOnly && (
        <SingleUploadImage
          onUpdateFile={props.uploadFunction}
          name={props.questionApiId}
        />
      )}
      {props.response?.images.map((image, index) => {
        return image.media_type === "image" ? (
          <S3Image s3Key={image.s3_url} alt="response" key={index} handleDelete={() => props.deleteImage(image.s3_url)} />
        ) : (
          <S3Video s3Key={image.s3_url} key={index} handleDelete={() => props.deleteImage(image.s3_url)} />
        );
      })}

    </Box>
  );
}

function DraftQuestion({
  question,
  loopApiId,
  readOnly = false,
  isGroupAdmin = false,
}: {
  question: PublicQuestion;
  loopApiId: string;
  readOnly?: boolean;
  isGroupAdmin?: boolean;
}): JSX.Element {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
  const showToast = useCustomToast();
  const deleteModal = useDisclosure();

  if (!currentUser) {
    return <Box>loading...</Box>;
  }
  const response = question.responses.find(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier
  );

  const isAuthor = question.author?.api_identifier === currentUser.api_identifier;
  const canDelete = isAuthor || isGroupAdmin;

  const deleteMutation = useMutation({
    ...deleteQuestionQuestionsQuestionQuestionApiIdDeleteMutation(),
    onSuccess: () => {
      showToast("Success!", "Question deleted successfully.", "success");
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      });
    },
    onError: (error: AxiosError<DeleteQuestionQuestionsQuestionQuestionApiIdDeleteError>) => {
      const errDetail =
        error.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    }
  });

  const handleDelete = async () => {
    await deleteMutation.mutateAsync({
      path: { question_api_id: question.api_identifier },
    });
    deleteModal.onClose();
  };

  const handleUpsert = async (responseText: string) => {
    await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_text: responseText,
        participant_api_identifier: currentUser.api_identifier,
      },
    });
  };

  const newHandleUpload = async (file: File) => {
    await uploadImageQuestionsQuestionQuestionApiIdUploadImagePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_image: file,
      },
    });
    queryClient.invalidateQueries({
      queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
        path: { letter_api_id: loopApiId },
      }),
    });
  };

  const handleDeleteImage = async (s3Url: string) => {
    try {
      // Optimistically update the UI
      queryClient.setQueryData(
        readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
        (oldData: any) => {
          if (!oldData) return oldData;

          // Create a deep copy and remove the image
          const updatedData = JSON.parse(JSON.stringify(oldData));

          // Find the response and remove the image
          updatedData.questions = updatedData.questions.map((q: any) => {
            if (q.api_identifier === question.api_identifier) {
              q.responses = q.responses.map((r: any) => {
                if (r.participant.api_identifier === currentUser.api_identifier) {
                  r.images = r.images.filter((img: any) => img.s3_url !== s3Url);
                }
                return r;
              });
            }
            return q;
          });

          return updatedData;
        }
      );

      // Make the API call
      await deleteImageResponsesResponseResponseApiIdDeleteImageDelete({
        path: { response_api_id: response!.api_identifier },
        query: {
          s3_url: s3Url,
        },
      });

      showToast("Success!", "Image deleted successfully.", "success");
    } catch (error) {
      console.error("Error deleting image:", error);

      // Revert optimistic update on error
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      });

      showToast("Error!", "Failed to delete image.", "error");
    }
  };

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
        deleteImage={handleDeleteImage}
        key={question.api_identifier}
        readOnly={readOnly}
      />

      <Modal isOpen={deleteModal.isOpen} onClose={deleteModal.onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete Question</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            Are you sure you want to delete this question? This action cannot be undone.
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
  );
}

export default DraftQuestion;
