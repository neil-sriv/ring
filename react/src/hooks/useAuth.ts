import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import type { AxiosError } from "axios"
import type {
  LoginAccessTokenLoginAccessTokenPostError,
  UserLinked,
} from "../client"
import {
  loginAccessTokenLoginAccessTokenPostMutation,
  readUserMePartiesMeGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../client/@tanstack/react-query.gen"
import { formatApiErrorDetail } from "../util/misc"

export interface AuthContext {
  isAuthenticated?: boolean
  user: UserLinked | undefined
}

const useAuth = (next?: string) => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    ...loginAccessTokenLoginAccessTokenPostMutation(),
    onSuccess: async (data) => {
      localStorage.setItem("access_token", data.access_token)
      // Auth failure redirects to /login without clearing the Query cache, so
      // a prior session's /me can still be warm. ensureQueryData would return
      // that stale user under the new JWT — drop it and force a fresh fetch
      // before navigating into the authenticated shell.
      queryClient.removeQueries({
        queryKey: readUserMePartiesMeGetQueryKey(),
      })
      await queryClient.fetchQuery({
        ...readUserMePartiesMeGetOptions(),
      })
      // Redirect to the next parameter if provided, otherwise go to home
      // Use TanStack Router's hash option to preserve hash fragments
      if (next) {
        // Parse the next URL to extract pathname, search, and hash
        const url = new URL(next, window.location.origin)
        const pathname = url.pathname
        const search = url.search
        const hash = url.hash.slice(1) // Remove the '#' character

        if (hash) {
          navigate({
            to: pathname + search,
            hash: hash,
          })
        } else {
          navigate({
            to: pathname + search,
          })
        }
      } else {
        navigate({ to: "/" })
      }
    },
    onError: (err: AxiosError<LoginAccessTokenLoginAccessTokenPostError>) => {
      setError(
        formatApiErrorDetail(
          err.response?.data?.detail,
          "Incorrect email or password",
        ),
      )
    },
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/login" })
  }

  return {
    loginMutation,
    logout,
    error,
    resetError: () => setError(null),
  }
}

export default useAuth
