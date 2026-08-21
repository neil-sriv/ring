import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { AxiosError } from "axios"
import type { ResetPasswordRequestResetPasswordRequestEmailPostError } from "../client"
import { resetPasswordRequestResetPasswordRequestEmailPost } from "../client/sdk.gen"
import useCustomToast from "../hooks/useCustomToast"
import { emailPattern, formatApiErrorDetail } from "../util/misc"

interface FormData {
  email: string
}

export const Route = createFileRoute("/reset-password")({
  component: ResetPasswordRequest,
  beforeLoad: async ({ context }) => {
    // Gate on a verified session, not on a leftover localStorage token: users
    // who need this page usually have an expired one sitting there.
    if (context.auth.isAuthenticated) {
      throw redirect({
        to: "/",
      })
    }
  },
})

function ResetPasswordRequest() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>()
  const showToast = useCustomToast()

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    try {
      await resetPasswordRequestResetPasswordRequestEmailPost({
        path: { email: data.email },
        throwOnError: true,
      })
      showToast(
        "Check your email.",
        "If an account exists for that address, we sent a link to reset your password.",
        "success",
      )
    } catch (err) {
      const axiosErr =
        err as AxiosError<ResetPasswordRequestResetPasswordRequestEmailPostError>
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(axiosErr.response?.data?.detail),
        "error",
      )
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="text-center">
          <RouterLink
            to="/"
            className="font-display text-3xl font-semibold tracking-tight text-foreground"
          >
            Ring
          </RouterLink>
          <h1 className="mt-6 text-lg font-semibold">Reset your password</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter your email and we&apos;ll send you a reset link.
          </p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-8 flex flex-col gap-5"
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              {...register("email", {
                required: "Email is required",
                pattern: emailPattern,
              })}
              placeholder="Email"
              type="email"
              className={errors.email ? "border-destructive" : ""}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            Continue
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
