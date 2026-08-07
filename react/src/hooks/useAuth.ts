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
} from "../client/@tanstack/react-query.gen"
import { formatApiErrorDetail } from "../util/misc"

export interface AuthContext {
  isAuthenticated?: boolean
  user: UserLinked | undefined
}

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = (next?: string) => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    ...loginAccessTokenLoginAccessTokenPostMutation(),
    onSuccess: (data) => {
      localStorage.setItem("access_token", data.access_token)
      queryClient.ensureQueryData({
        ...readUserMePartiesMeGetOptions({}),
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

export { isLoggedIn }
export default useAuth
