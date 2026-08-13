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
import { Check, Loader2, Trash2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import {
  type DeleteQuestionQuestionsQuestionQuestionApiIdDeleteError,
  type PublicLetter,
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

type DraftSaveStatus = "idle" | "saving" | "saved" | "error"

function DraftSaveStatusLine({ status }: { status: DraftSaveStatus }) {
  switch (status) {
    case "idle":
      return null
    case "saving":
      return (
        <div
          className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground"
          role="status"
          aria-live="polite"
        >
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Saving...
        </div>
      )
    case "saved":
      return (
        <div
          className="mt-1 flex items-center gap-1.5 text-sm text-green-600 dark:text-green-400"
          role="status"
          aria-live="polite"
        >
          <Check className="h-3.5 w-3.5" />
          Saved
        </div>
      )
    case "error":
      return (
        <div
          className="mt-1 flex items-center gap-1.5 text-sm text-destructive"
          role="status"
          aria-live="polite"
        >
          Couldn't save
        </div>
      )
    default: {
      const _exhaustive: never = status
      return _exhaustive
    }
  }
}

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(
    props.response?.response_text ?? "",
  )
  const [saveStatus, setSaveStatus] = useState<DraftSaveStatus>("idle")
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const savingStartTimeRef = useRef<number | null>(null)
  const lastSavedTextRef = useRef(props.response?.response_text ?? "")
  const responseTextRef = useRef(responseText)
  const saveSeqRef = useRef(0)
  const flushInFlightRef = useRef<string | null>(null)
  const submitResponseRef = useRef(props.submitResponse)
  const showToast = useCustomToast()
  const textareaRef = useAutoResizeTextarea(responseText)

  responseTextRef.current = responseText
  submitResponseRef.current = props.submitResponse

  // Don't clobber in-progress typing when letter props refresh.
  useEffect(() => {
    const nextText = props.response?.response_text ?? ""
    if (responseTextRef.current !== lastSavedTextRef.current) {
      return
    }
    setResponseText(nextText)
    lastSavedTextRef.current = nextText
  }, [props.response?.response_text])

  const persistResponse = async (
    newValue: string,
    { showStatus }: { showStatus: boolean },
  ) => {
    if (newValue === lastSavedTextRef.current) {
      return
    }

    const seq = ++saveSeqRef.current
    if (showStatus) {
      savingStartTimeRef.current = Date.now()
      setSaveStatus("saving")
    }
    try {
      await submitResponseRef.current(newValue)
      if (saveSeqRef.current === seq) {
        lastSavedTextRef.current = newValue
      }
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: unknown }>
      if (showStatus) {
        showToast(
          "Error!",
          formatApiErrorDetail(
            axiosError.response?.data?.detail,
            "Failed to save answer.",
          ),
          "error",
        )
        if (
          saveSeqRef.current === seq &&
          responseTextRef.current === newValue
        ) {
          setSaveStatus("error")
        }
      }
      throw error
    }

    if (!showStatus) {
      return
    }

    // Ensure saving animation shows for at least 250ms
    const elapsed = Date.now() - (savingStartTimeRef.current || 0)
    const remainingTime = Math.max(0, 250 - elapsed)
    if (remainingTime > 0) {
      await new Promise((resolve) => setTimeout(resolve, remainingTime))
    }
    if (saveSeqRef.current === seq && responseTextRef.current === newValue) {
      setSaveStatus("saved")
    }
  }

  const flushPendingSave = () => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
      debounceTimeoutRef.current = null
    }
    const pending = responseTextRef.current
    if (pending === lastSavedTextRef.current) {
      return
    }
    if (flushInFlightRef.current === pending) {
      return
    }
    flushInFlightRef.current = pending
    void persistResponse(pending, { showStatus: false })
      .catch(() => {
        // Best-effort flush on navigate/unload; status UI may be unmounted.
      })
      .finally(() => {
        if (flushInFlightRef.current === pending) {
          flushInFlightRef.current = null
        }
      })
  }
  const flushPendingSaveRef = useRef(flushPendingSave)
  flushPendingSaveRef.current = flushPendingSave

  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setResponseText(newValue)
    setSaveStatus(newValue === lastSavedTextRef.current ? "saved" : "idle")

    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // Set new timeout for debounced save
    debounceTimeoutRef.current = setTimeout(() => {
      void persistResponse(newValue, { showStatus: true }).catch(() => {
        // Error toast + status handled inside persistResponse when showStatus.
      })
    }, 1000) // 1 second debounce
  }

  // Flush pending debounce on navigate away or tab close — clearing alone
  // previously dropped unsaved draft text typed within the debounce window.
  useEffect(() => {
    const onPageHide = () => {
      flushPendingSaveRef.current()
    }
    window.addEventListener("pagehide", onPageHide)
    return () => {
      window.removeEventListener("pagehide", onPageHide)
      flushPendingSaveRef.current()
    }
  }, [])

  const isSaving = saveStatus === "saving"

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
      {!props.readOnly && <DraftSaveStatusLine status={saveStatus} />}
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

  const letterQueryKey = readLetterLettersLetterLetterApiIdGetQueryKey({
    path: { letter_api_id: loopApiId },
  })

  const handleUpsert = async (responseText: string): Promise<void> => {
    const { data: updatedQuestion } =
      await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
        path: { question_api_id: question.api_identifier },
        body: {
          response_text: responseText,
          participant_api_identifier: currentUser.api_identifier,
        },
        throwOnError: true,
      })

    // Keep letter cache in sync so navigate-away → return within staleTime
    // still shows the saved text (debounce and unmount flush).
    let didPatch = false
    queryClient.setQueryData<PublicLetter>(letterQueryKey, (oldData) => {
      if (!oldData) {
        return oldData
      }

      return {
        ...oldData,
        questions: oldData.questions.map((q) => {
          if (q.api_identifier !== question.api_identifier) {
            return q
          }

          const existingIdx = q.responses.findIndex(
            (r) => r.participant.api_identifier === currentUser.api_identifier,
          )
          if (existingIdx >= 0) {
            const responses = [...q.responses]
            responses[existingIdx] = {
              ...responses[existingIdx],
              response_text: responseText,
            }
            didPatch = true
            return { ...q, responses }
          }

          // Upsert returns ResponseUnlinked (no participant). Require both an
          // unknown id and matching text so we don't attach another member's
          // response to currentUser when the letter cache lags the payload.
          const knownIds = new Set(q.responses.map((r) => r.api_identifier))
          const created = updatedQuestion?.responses.find(
            (r) =>
              !knownIds.has(r.api_identifier) &&
              r.response_text === responseText,
          )
          if (!created) {
            return q
          }

          didPatch = true
          return {
            ...q,
            responses: [
              ...q.responses,
              {
                ...created,
                participant: {
                  email: currentUser.email,
                  name: currentUser.name,
                  api_identifier: currentUser.api_identifier,
                  admin: currentUser.admin,
                },
                images: [],
              },
            ],
          }
        }),
      }
    })

    if (!didPatch) {
      await queryClient.invalidateQueries({ queryKey: letterQueryKey })
    }
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
