import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import type { AxiosError } from "axios"
import type { RegisterUserPartiesRegisterTokenPostError } from "../client"
import { registerUserPartiesRegisterTokenPostMutation } from "../client/@tanstack/react-query.gen"
import { formatApiErrorDetail } from "../util/misc"

const useRegister = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const registerMutation = useMutation({
    ...registerUserPartiesRegisterTokenPostMutation(),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: (err: AxiosError<RegisterUserPartiesRegisterTokenPostError>) => {
      setError(
        formatApiErrorDetail(
          err.response?.data?.detail,
          "Registration failed. Please try again.",
        ),
      )
    },
  })

  return {
    registerMutation,
    error,
    resetError: () => setError(null),
  }
}

export default useRegister
