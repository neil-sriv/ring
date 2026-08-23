import { useMutation } from "@tanstack/react-query"
import {
  Link as RouterLink,
  createFileRoute,
  useNavigate,
} from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { RingMark } from "@/components/Common/RingMark"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { AxiosError } from "axios"
import type {
  NewPassword,
  ResetPasswordResetPasswordTokenPostError,
} from "../../client"
import { resetPasswordResetPasswordTokenPostMutation } from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import {
  confirmPasswordRules,
  formatApiErrorDetail,
  passwordRules,
} from "../../util/misc"

interface NewPasswordForm extends NewPassword {
  confirm_password: string
}

export const Route = createFileRoute("/reset-password/$token")({
  component: ResetPassword,
})

function ResetPassword() {
  const {
    register,
    handleSubmit,
    getValues,
    reset,
    formState: { errors },
  } = useForm<NewPasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      new_password: "",
    },
  })
  const showToast = useCustomToast()
  const navigate = useNavigate()
  const { token } = Route.useParams()

  const mutation = useMutation({
    ...resetPasswordResetPasswordTokenPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Password updated.", "success")
      reset()
      navigate({ to: "/login" })
    },
    onError: (err: AxiosError<ResetPasswordResetPasswordTokenPostError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
  })

  const onSubmit: SubmitHandler<NewPasswordForm> = async (data) => {
    if (!token) return
    mutation.mutate({
      path: { token: token },
      body: data,
    })
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="text-center">
          <RouterLink
            to="/"
            className="inline-flex flex-col items-center gap-3 font-display text-3xl font-semibold tracking-tight text-foreground"
          >
            <RingMark className="h-10 w-10 text-primary" />
            Ring
          </RouterLink>
          <h1 className="mt-6 text-lg font-semibold">Choose a new password</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter and confirm the new password for your account.
          </p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-8 flex flex-col gap-5"
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              {...register("new_password", passwordRules())}
              placeholder="Password"
              type="password"
              className={errors.new_password ? "border-destructive" : ""}
            />
            {errors.new_password && (
              <p className="text-xs text-destructive">
                {errors.new_password.message}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="confirm_password">Confirm Password</Label>
            <Input
              id="confirm_password"
              {...register("confirm_password", confirmPasswordRules(getValues))}
              placeholder="Confirm password"
              type="password"
              className={errors.confirm_password ? "border-destructive" : ""}
            />
            {errors.confirm_password && (
              <p className="text-xs text-destructive">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            disabled={mutation.isPending}
            className="w-full"
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Reset Password
          </Button>

          <div className="text-center">
            <RouterLink
              to="/login"
              className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              Back to login
            </RouterLink>
          </div>
        </form>
      </div>
    </div>
  )
}
