import { useMutation, useQuery } from "@tanstack/react-query"
import type { AxiosError } from "axios"

import {
  readSpotifyStatusSpotifyStatusGetOptions,
  startSpotifyAuthorizationSpotifyAuthorizePostMutation,
} from "@/client/@tanstack/react-query.gen"
import useCustomToast from "@/hooks/useCustomToast"
import { formatApiErrorDetail } from "@/util/misc"

export function useSpotifyAccount() {
  const showToast = useCustomToast()
  const statusQuery = useQuery({
    ...readSpotifyStatusSpotifyStatusGetOptions(),
  })
  const authorize = useMutation({
    ...startSpotifyAuthorizationSpotifyAuthorizePostMutation(),
  })

  async function startLink(returnTo: string) {
    try {
      const result = await authorize.mutateAsync({
        body: { return_to: returnTo },
      })
      window.location.assign(result.authorization_url)
    } catch (err) {
      showToast(
        "Spotify",
        formatApiErrorDetail(
          (err as AxiosError<{ detail?: unknown }>).response?.data?.detail,
        ),
        "error",
      )
    }
  }

  return {
    statusQuery,
    startLink,
    isStartingLink: authorize.isPending,
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
