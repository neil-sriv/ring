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
    await mutation.mutateAsync({
      body: data,
    })
  }

  const isSaving = isSubmitting || mutation.isPending

  return (
    <div className="w-full">
      <h3 className="text-base font-semibold">Change password</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Use a long password you don't use anywhere else.
      </p>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mt-5 flex max-w-md flex-col gap-5"
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="current_password">Current password</Label>
          <Input
            id="current_password"
            {...register("current_password")}
            placeholder="Password"
            type="password"
          />
          {errors.current_password && (
            <p className="text-xs text-destructive">
              {errors.current_password.message}
            </p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">New password</Label>
          <Input
            id="password"
            {...register("new_password", passwordRules())}
            placeholder="Password"
            type="password"
          />
          {errors.new_password && (
            <p className="text-xs text-destructive">
              {errors.new_password.message}
            </p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="confirm_password">Confirm password</Label>
          <Input
            id="confirm_password"
            {...register("confirm_password", confirmPasswordRules(getValues))}
            placeholder="Password"
            type="password"
          />
          {errors.confirm_password && (
            <p className="text-xs text-destructive">
              {errors.confirm_password.message}
            </p>
          )}
        </div>
        <div>
          <Button type="submit" disabled={isSaving}>
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            Save
          </Button>
        </div>
      </form>
    </div>
  )
}

export default ChangePassword
