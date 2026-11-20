import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import type {
  AddQuestionLettersLetterLetterApiIdAddQuestionPostError,
  PublicLetter,
} from "../../client"
import {
  addQuestionLettersLetterLetterApiIdAddQuestionPostMutation,
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listLettersLettersLettersGetQueryKey,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  readUserMePartiesMeGetOptions,
} from "../../client/@tanstack/react-query.gen"
import { useAutoResizeTextarea } from "../../hooks/useAutoResizeTextarea"
import useCustomToast from "../../hooks/useCustomToast"
import { useSubmitOnce } from "../../hooks/useSubmitOnce"
import {
  LATE_QUESTION_CUTOFF_REASON,
  lateQuestionReplyNotice,
} from "../../util/lateQuestion"
import { formatApiErrorDetail } from "../../util/misc"

interface AddLateQuestionProps {
  loop: PublicLetter
  /** Client-side cutoff. The server still rejects a late submit. */
  disabled?: boolean
  onAdded?: () => void
}

function AddLateQuestion({
  loop,
  disabled = false,
  onAdded,
}: AddLateQuestionProps): JSX.Element {
  const queryClient = useQueryClient()
  const { data: currentUser } = useQuery({
    ...readUserMePartiesMeGetOptions(),
  })
  const showToast = useCustomToast()
  const [questionText, setQuestionText] = useState("")
  const textareaRef = useAutoResizeTextarea(questionText)
  const submitOnce = useSubmitOnce()

  const mutation = useMutation({
    ...addQuestionLettersLetterLetterApiIdAddQuestionPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Your late question has been added.", "success")
      setQuestionText("")
      onAdded?.()
    },
    onError: (
      err: AxiosError<AddQuestionLettersLetterLetterApiIdAddQuestionPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(
          err.response?.data?.detail,
          "Failed to add a late question. Please try again.",
        ),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
      })
      queryClient.invalidateQueries({
        queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
      })
      queryClient.invalidateQueries({
        queryKey: listLettersLettersLettersGetQueryKey({
          query: { group_api_id: loop.group.api_identifier },
        }),
      })
    },
  })

  const isSaving = mutation.isPending || submitOnce.pending
  const fieldsDisabled = disabled || isSaving
  const notice = lateQuestionReplyNotice(loop, currentUser?.api_identifier)

  const handleSubmit = async () => {
    if (disabled || !currentUser || !questionText.trim()) {
      return
    }
    await submitOnce.run(async () => {
      try {
        await mutation.mutateAsync({
          body: {
            question_text: questionText.trim(),
            // The current API stores this field. Send the signed-in member,
            // never someone else, so a server that records the caller instead
            // still accepts the request.
            author_api_id: currentUser.api_identifier,
          },
          path: { letter_api_id: loop.api_identifier },
        })
      } catch {
        // onError already toasts the server message, including a cutoff 400.
      }
    })
  }

  return (
    <div className="my-5 rounded-lg border bg-muted/50 p-4 sm:p-5">
      <div className="space-y-1">
        {disabled && (
          <p className="text-sm font-medium">{LATE_QUESTION_CUTOFF_REASON}</p>
        )}
        <p className="text-sm text-muted-foreground">{notice}</p>
      </div>
      <form
        className="mt-4"
        onSubmit={(event) => {
          event.preventDefault()
          void handleSubmit()
        }}
      >
        <Textarea
          ref={textareaRef}
          value={questionText}
          onChange={(event) => setQuestionText(event.target.value)}
          placeholder="What should everyone answer?"
          aria-label="What should everyone answer?"
          className="min-h-[100px] overflow-hidden resize-none"
          disabled={fieldsDisabled}
        />
        <Button
          type="submit"
          className="mt-3"
          disabled={fieldsDisabled || !questionText.trim() || !currentUser}
        >
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isSaving ? "Adding..." : "Add Late Question"}
        </Button>
      </form>
    </div>
  )
}

interface LateQuestionBannerProps {
  cutoffReached: boolean
  composerOpen: boolean
  onToggle: () => void
}

export function LateQuestionBanner({
  cutoffReached,
  composerOpen,
  onToggle,
}: LateQuestionBannerProps): JSX.Element {
  return (
    <div
      className={`rounded-lg border p-4 ${
        cutoffReached
          ? "border-border bg-muted/40"
          : "border-info/25 bg-info/10"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Forgot to ask something?</p>
          <p className="text-sm text-muted-foreground">
            {cutoffReached
              ? LATE_QUESTION_CUTOFF_REASON
              : "Anyone in the group can add one until a day before this loop sends."}
          </p>
        </div>
        <Button
          type="button"
          variant={composerOpen ? "default" : "outline"}
          onClick={onToggle}
          disabled={cutoffReached}
          aria-expanded={composerOpen}
        >
          {composerOpen ? "Hide late question" : "Add a late question"}
        </Button>
      </div>
    </div>
  )
}

export default AddLateQuestion
