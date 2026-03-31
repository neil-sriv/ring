import { createFileRoute, redirect } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { isLoggedIn } from "../hooks/useAuth"
import useCustomToast from "../hooks/useCustomToast"
import { emailPattern } from "../util/misc"
import { resetPasswordRequestResetPasswordRequestEmailPost } from "../client/sdk.gen"
import { ResetPasswordRequestResetPasswordRequestEmailPostError } from "../client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface FormData {
  email: string
}

export const Route = createFileRoute("/reset-password")({
  component: ResetPasswordRequest,
  beforeLoad: async () => {
    if (isLoggedIn()) {
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
    await resetPasswordRequestResetPasswordRequestEmailPost({
      path: { email: data.email },
    })
      .then(() => {
        showToast(
          "Email sent.",
          "We sent an email with a link to get back into your account.",
          "success",
        )
      })
      .catch((err: ResetPasswordRequestResetPasswordRequestEmailPostError) => {
        const errDetail =
          err.detail || "no error detail, please contact support"
        showToast("Something went wrong.", `${errDetail}`, "error")
      })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary/10 via-background to-muted p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold tracking-tight text-primary">
            Password Reset
          </CardTitle>
          <CardDescription>
            A password reset email will be sent to the registered account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="space-y-2">
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
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Continue
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
