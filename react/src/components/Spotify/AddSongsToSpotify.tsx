import { Button } from "@/components/ui/button"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect, useRef } from "react"

import { saveLetterTracksToSpotifyLibrarySpotifyLettersLetterApiIdLibraryPostMutation } from "@/client/@tanstack/react-query.gen"
import useCustomToast from "@/hooks/useCustomToast"
import { useSubmitOnce } from "@/hooks/useSubmitOnce"
import { formatApiErrorDetail } from "@/util/misc"
import {
  axiosDetail,
  axiosStatus,
  useSpotifyAccount,
} from "./useSpotifyAccount"

interface AddSongsToSpotifyProps {
  loopApiId: string
  spotify?: string
  spotifyAction?: string
  spotifyError?: string
}

function unavailableMessage() {
  return (
    <p className="text-sm text-muted-foreground">
      Spotify linking is unavailable. This server has no Spotify app configured.
    </p>
  )
}

export function AddSongsToSpotify({
  loopApiId,
  spotify,
  spotifyAction,
  spotifyError,
}: AddSongsToSpotifyProps) {
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const { statusQuery, startLink, isStartingLink } = useSpotifyAccount()
  const submitOnce = useSubmitOnce()
  const handledReturn = useRef(false)
  const save = useMutation({
    ...saveLetterTracksToSpotifyLibrarySpotifyLettersLetterApiIdLibraryPostMutation(),
    onSuccess: (data) => {
      if (data.saved_count === 0) {
        showToast("Spotify", "This letter has no Spotify tracks.", "success")
        return
      }
      const noun = data.saved_count === 1 ? "song" : "songs"
      showToast(
        "Spotify",
        `Saved ${data.saved_count} ${noun} to your Spotify library.`,
        "success",
      )
    },
    onError: (err) => {
      if (
        axiosStatus(err) === 409 &&
        axiosDetail(err) === "spotify_not_linked"
      ) {
        void startLink(`/loops/${loopApiId}?spotify_action=save`)
        return
      }
      showToast("Spotify", formatApiErrorDetail(axiosDetail(err)), "error")
    },
  })

  useEffect(() => {
    if (handledReturn.current || !spotify) {
      return
    }
    handledReturn.current = true
    void navigate({
      to: "/loops/$loopId",
      params: { loopId: loopApiId },
      search: {},
      replace: true,
    })
    if (spotify === "error") {
      showToast(
        "Spotify",
        spotifyError === "access_denied"
          ? "Spotify linking was canceled."
          : "Spotify linking failed.",
        "error",
      )
      return
    }
    if (spotify === "linked" && spotifyAction === "save") {
      void submitOnce.run(async () => {
        try {
          await save.mutateAsync({ path: { letter_api_id: loopApiId } })
        } catch {
          // onError already toasts or starts linking
        }
      })
    }
  }, [
    loopApiId,
    navigate,
    save,
    showToast,
    submitOnce.run,
    spotify,
    spotifyAction,
    spotifyError,
  ])

  if (statusQuery.isLoading) {
    return null
  }
  if (!statusQuery.data?.configured) {
    return unavailableMessage()
  }

  const pending = isStartingLink || save.isPending || submitOnce.pending

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        type="button"
        variant="outline"
        disabled={pending}
        onClick={() => {
          if (!statusQuery.data?.linked) {
            void startLink(`/loops/${loopApiId}?spotify_action=save`)
            return
          }
          void submitOnce.run(async () => {
            try {
              await save.mutateAsync({ path: { letter_api_id: loopApiId } })
            } catch {
              // onError already toasts or starts linking
            }
          })
        }}
      >
        Add these songs to your Spotify account
      </Button>
    </div>
  )
}
