import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useState } from "react"

import type {
  PublicLetter,
  SendLetterNowLettersLetterLetterApiIdSendNowPostError,
} from "../../client"
import {
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listLettersLettersLettersGetQueryKey,
  readLetterLettersLetterLetterApiIdGetQueryKey,
  sendLetterNowLettersLetterLetterApiIdSendNowPostMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { useSubmitOnce } from "../../hooks/useSubmitOnce"
import { formatApiErrorDetail } from "../../util/misc"
import { getParticipantReplyStatuses } from "./LoopReplyTracker"

function countRespondedMembers(loop: PublicLetter): {
  responded: number
  members: number
} {
  const memberIds = new Set(
    loop.participants.map((participant) => participant.api_identifier),
  )
  const responded = getParticipantReplyStatuses(loop).filter(
    (status) =>
      status.hasReplied && memberIds.has(status.participant.api_identifier),
  ).length
  return { responded, members: memberIds.size }
}

const SEND_LETTER_NOW_TIMEOUT_MS = 20_000

function respondedMembersSentence(responded: number, members: number): string {
  const memberWord = members === 1 ? "member" : "members"
  const verb = responded === 1 ? "has" : "have"
  return `${responded} of ${members} ${memberWord} ${verb} responded so far.`
}

export function SendLetterNow({
  loop,
  isGroupAdmin,
}: {
  loop: PublicLetter
  isGroupAdmin: boolean
}) {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const submitOnce = useSubmitOnce()
  const [open, setOpen] = useState(false)
  const { responded, members } = countRespondedMembers(loop)

  const mutation = useMutation({
    ...sendLetterNowLettersLetterLetterApiIdSendNowPostMutation(),
    onSuccess: (data) => {
      queryClient.setQueryData(
        readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
        data,
      )
      showToast("Success!", "Loop sent.", "success")
      setOpen(false)
    },
    onError: (
      err: AxiosError<SendLetterNowLettersLetterLetterApiIdSendNowPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
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
        queryKey: listLettersLettersLettersGetQueryKey({
          query: { group_api_id: loop.group.api_identifier },
        }),
      })
      queryClient.invalidateQueries({
        queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
      })
    },
  })

  if (!isGroupAdmin || loop.status !== "IN_PROGRESS") {
    return null
  }

  const isSaving = mutation.isPending || submitOnce.pending

  const onConfirm = () => {
    void submitOnce.run(async () => {
      try {
        await mutation.mutateAsync({
          path: { letter_api_id: loop.api_identifier },
          timeout: SEND_LETTER_NOW_TIMEOUT_MS,
        })
      } catch {
        // onError already toasts.
      }
    })
  }

  return (
    <>
      <Button type="button" onClick={() => setOpen(true)} disabled={isSaving}>
        Send now
      </Button>
      <AlertDialog
        open={open}
        onOpenChange={(next) => {
          if (!next && !isSaving) {
            setOpen(false)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Send this loop now?</AlertDialogTitle>
            <AlertDialogDescription>
              {respondedMembersSentence(responded, members)} Sending now emails
              this loop to the group.
              {loop.letter_type === "CYCLIC"
                ? " The next loop will be scheduled."
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button type="button" onClick={onConfirm} disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
              Send now
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
