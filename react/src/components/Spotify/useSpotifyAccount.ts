import { useMutation, useQuery } from "@tanstack/react-query"
import { AxiosError } from "axios"

import {
  readSpotifyStatusSpotifyStatusGetOptions,
  startSpotifyAuthorizationSpotifyAuthorizePostMutation,
} from "@/client/@tanstack/react-query.gen"
import useCustomToast from "@/hooks/useCustomToast"
import { useSubmitOnce } from "@/hooks/useSubmitOnce"
import { formatApiErrorDetail } from "@/util/misc"

// Authorize only returns a redirect URL; keep a short bound so Link stays unlockable.
export const SPOTIFY_AUTHORIZE_TIMEOUT_MS = 20_000

export function useSpotifyAccount() {
  const showToast = useCustomToast()
  const statusQuery = useQuery({
    ...readSpotifyStatusSpotifyStatusGetOptions(),
  })
  const authorize = useMutation({
    ...startSpotifyAuthorizationSpotifyAuthorizePostMutation(),
  })
  const submitOnce = useSubmitOnce()

  async function startLink(returnTo: string) {
    await submitOnce.run(async () => {
      try {
        const result = await authorize.mutateAsync({
          body: { return_to: returnTo },
          timeout: SPOTIFY_AUTHORIZE_TIMEOUT_MS,
        })
        window.location.assign(result.authorization_url)
      } catch (err) {
        showToast("Spotify", spotifyErrorMessage(err), "error")
      }
    })
  }

  return {
    statusQuery,
    startLink,
    isStartingLink: authorize.isPending || submitOnce.pending,
  }
}

export function axiosStatus(err: unknown): number | undefined {
  if (!err || typeof err !== "object" || !("response" in err)) {
    return undefined
  }
  return (err as AxiosError).response?.status
}

export function axiosDetail(err: unknown): string | undefined {
  if (!err || typeof err !== "object" || !("response" in err)) {
    return undefined
  }
  const detail = (err as AxiosError<{ detail?: unknown }>).response?.data
    ?.detail
  if (typeof detail === "string") {
    return detail
  }
  return undefined
}

/** Axios sets code ECONNABORTED when `timeout` fires with no response. */
export function isAxiosTimeout(err: unknown): boolean {
  return err instanceof AxiosError && err.code === AxiosError.ECONNABORTED
}

export function spotifyErrorMessage(err: unknown): string {
  if (isAxiosTimeout(err)) {
    return "Spotify request timed out. Please try again."
  }
  return formatApiErrorDetail(axiosDetail(err))
}
