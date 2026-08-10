import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Loader2, Trash2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import {
  type DeleteQuestionQuestionsQuestionQuestionApiIdDeleteError,
  type PublicQuestion,
  type ResponseWithParticipant,
  type UserLinked,
  deleteImageResponsesResponseResponseApiIdDeleteImageDelete,
  uploadImageQuestionsQuestionQuestionApiIdUploadImagePost,
  upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost,
} from "../../client"
import {
  deleteQuestionQuestionsQuestionQuestionApiIdDeleteMutation,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { useAutoResizeTextarea } from "../../hooks/useAutoResizeTextarea"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"
import {
  S3Image,
  S3Video,
  SingleUploadImage,
} from "../Common/SingleUploadImage"

type ResponseBlockProps = {
  uploadFunction: (file: File) => Promise<void>
  deleteImage: (s3Url: string) => Promise<void>
  questionApiId: string
  response?: ResponseWithParticipant
  submitResponse: (responseText: string) => Promise<void>
  readOnly?: boolean
}

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(
    props.response?.response_text ?? "",
  )
  const [isSaving, setIsSaving] = useState(false)
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const savingStartTimeRef = useRef<number | null>(null)
  const lastSavedTextRef = useRef(props.response?.response_text ?? "")
  const showToast = useCustomToast()
  const textareaRef = useAutoResizeTextarea(responseText)

  // Update local state when response prop changes
  useEffect(() => {
    const nextText = props.response?.response_text ?? ""
    setResponseText(nextText)
    lastSavedTextRef.current = nextText
  }, [props.response?.response_text])

  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setResponseText(newValue)

    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // Set new timeout for debounced save
    debounceTimeoutRef.current = setTimeout(async () => {
      if (newValue !== lastSavedTextRef.current) {
        savingStartTimeRef.current = Date.now()
        setIsSaving(true)
        try {
          await props.submitResponse(newValue)
          lastSavedTextRef.current = newValue
          // Inline "Saving..." is enough for autosave; avoid toast spam.
        } catch (error) {
          const axiosError = error as AxiosError<{ detail?: unknown }>
          showToast(
            "Error!",
            formatApiErrorDetail(
              axiosError.response?.data?.detail,
              "Failed to save answer.",
            ),
            "error",
          )
        } finally {
          // Ensure saving animation shows for at least 250ms
          const elapsed = Date.now() - (savingStartTimeRef.current || 0)
          const remainingTime = Math.max(0, 250 - elapsed)

          setTimeout(() => {
            setIsSaving(false)
          }, remainingTime)
        }
      }
    }, 1000) // 1 second debounce
  }

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div className="my-2.5">
      <Textarea
        ref={textareaRef}
        value={responseText}
        onChange={handleResponseChange}
        disabled={props.readOnly}
        placeholder={isSaving ? "Saving..." : "Type your response..."}
        className={`overflow-hidden resize-none bg-muted transition-opacity duration-200 ${
          isSaving ? "opacity-70" : "opacity-100"
        }`}
      />
      {isSaving && (
        <div className="text-sm text-muted-foreground mt-1">Saving...</div>
      )}
      {!props.readOnly && (
        <SingleUploadImage
          onUpdateFile={props.uploadFunction}
          name={props.questionApiId}
        />
      )}
      {props.response?.images.map((image, index) => {
        return image.media_type === "image" ? (
          <S3Image
            s3Key={image.s3_url}
            alt="response"
            key={index}
            handleDelete={() => props.deleteImage(image.s3_url)}
          />
        ) : (
          <S3Video
            s3Key={image.s3_url}
            key={index}
            handleDelete={() => props.deleteImage(image.s3_url)}
          />
        )
      })}
    </div>
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
  const [deleteOpen, setDeleteOpen] = useState(false)

  if (!currentUser) {
    return <div>loading...</div>
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
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(error.response?.data?.detail),
        "error",
      )
    },
  })

  const handleDelete = async () => {
    await deleteMutation.mutateAsync({
      path: { question_api_id: question.api_identifier },
    })
    setDeleteOpen(false)
  }

  const handleUpsert = async (responseText: string): Promise<void> => {
    await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_text: responseText,
        participant_api_identifier: currentUser.api_identifier,
      },
      throwOnError: true,
    })
  }

  const newHandleUpload = async (file: File) => {
    try {
      await uploadImageQuestionsQuestionQuestionApiIdUploadImagePost({
        path: { question_api_id: question.api_identifier },
        body: {
          response_image: file,
        },
        throwOnError: true,
      })
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      })
      showToast("Success!", "Image uploaded successfully.", "success")
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: unknown }>
      showToast(
        "Error!",
        formatApiErrorDetail(
          axiosError.response?.data?.detail,
          "Failed to upload image.",
        ),
        "error",
      )
      throw error
    }
  }

  const handleDeleteImage = async (s3Url: string) => {
    try {
      // Optimistically update the UI
      queryClient.setQueryData(
        readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
        (oldData: any) => {
          if (!oldData) return oldData

          // Create a deep copy and remove the image
          const updatedData = JSON.parse(JSON.stringify(oldData))

          // Find the response and remove the image
          updatedData.questions = updatedData.questions.map((q: any) => {
            if (q.api_identifier === question.api_identifier) {
              q.responses = q.responses.map((r: any) => {
                if (
                  r.participant.api_identifier === currentUser.api_identifier
                ) {
                  r.images = r.images.filter((img: any) => img.s3_url !== s3Url)
                }
                return r
              })
            }
            return q
          })

          return updatedData
        },
      )

      // Make the API call
      await deleteImageResponsesResponseResponseApiIdDeleteImageDelete({
        path: { response_api_id: response!.api_identifier },
        query: {
          s3_url: s3Url,
        },
        throwOnError: true,
      })

      showToast("Success!", "Image deleted successfully.", "success")
    } catch (error) {
      // Revert optimistic update on error
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loopApiId },
        }),
      })

      const axiosError = error as AxiosError<{ detail?: unknown }>
      showToast(
        "Error!",
        formatApiErrorDetail(
          axiosError.response?.data?.detail,
          "Failed to delete image.",
        ),
        "error",
      )
    }
  }

  return (
    <div className="my-5">
      <div className="flex justify-between items-center">
        {question.author == null ? (
          <h3 className="text-lg font-semibold">{question.question_text}</h3>
        ) : (
          <h3 className="text-lg font-semibold">
            {question.author.name} asked: {question.question_text}
          </h3>
        )}
        {canDelete && readOnly && (
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        )}
      </div>
      <ResponseBlock
        questionApiId={question.api_identifier}
        response={response}
        submitResponse={handleUpsert}
        uploadFunction={newHandleUpload}
        deleteImage={handleDeleteImage}
        key={question.api_identifier}
        readOnly={readOnly}
      />

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Question</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this question? This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default DraftQuestion
