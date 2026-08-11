import { useMutation } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  UpdatePasswordMePartiesMePasswordPatchError,
  UserUpdatePassword,
} from "../../client"
import { updatePasswordMePartiesMePasswordPatchMutation } from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import {
  confirmPasswordRules,
  formatApiErrorDetail,
  passwordRules,
} from "../../util/misc"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface UpdatePasswordForm extends UserUpdatePassword {
  confirm_password: string
}

const ChangePassword = () => {
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UpdatePasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
  })

  const mutation = useMutation({
    ...updatePasswordMePartiesMePasswordPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "Password updated.", "success")
      reset()
    },
    onError: (err: AxiosError<UpdatePasswordMePartiesMePasswordPatchError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
  })

  const onSubmit: SubmitHandler<UpdatePasswordForm> = async (data) => {
    mutation.mutate({
      body: data,
    })
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-6">
        <h3 className="text-sm font-semibold text-foreground">
          Change Password
        </h3>
        <Card className="w-full md:w-1/2">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current_password">Current Password</Label>
                <Input
                  id="current_password"
                  {...register("current_password")}
                  placeholder="Password"
                  type="password"
                />
                {errors.current_password && (
                  <p className="text-sm text-destructive">
                    {errors.current_password.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Set Password</Label>
                <Input
                  id="password"
                  {...register("new_password", passwordRules())}
                  placeholder="Password"
                  type="password"
                />
                {errors.new_password && (
                  <p className="text-sm text-destructive">
                    {errors.new_password.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm Password</Label>
                <Input
                  id="confirm_password"
                  {...register(
                    "confirm_password",
                    confirmPasswordRules(getValues),
                  )}
                  placeholder="Password"
                  type="password"
                />
                {errors.confirm_password && (
                  <p className="text-sm text-destructive">
                    {errors.confirm_password.message}
                  </p>
                )}
              </div>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Save
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default ChangePassword
