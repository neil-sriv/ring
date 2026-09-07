import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type { CreateUserPartiesUserPostError, UserCreate } from "../../client"
import {
  createUserPartiesUserPostMutation,
  readUsersPartiesUsersGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { emailPattern, formatApiErrorDetail } from "../../util/misc"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface AddUserProps {
  isOpen: boolean
  onClose: () => void
}

interface UserCreateForm extends UserCreate {
  confirm_password: string
}

const freshDefaults = (): UserCreateForm => ({
  email: "",
  name: "",
  password: "",
  confirm_password: "",
  // is_superuser: false,
  // is_active: false,
})

const AddUser = ({ isOpen, onClose }: AddUserProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UserCreateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: freshDefaults(),
  })

  // Parent keeps this dialog mounted; clear credentials each open.
  useEffect(() => {
    if (isOpen) {
      reset(freshDefaults(), {
        keepErrors: false,
        keepDirty: false,
        keepTouched: false,
      })
    }
  }, [isOpen, reset])

  const mutation = useMutation({
    ...createUserPartiesUserPostMutation(),
    onSuccess: () => {
      showToast("Success!", "User created successfully.", "success")
      reset(freshDefaults())
      onClose()
    },
    onError: (error: AxiosError<CreateUserPartiesUserPostError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(error.response?.data?.detail),
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserCreateForm> = (data) => {
    mutation.mutate({
      body: data,
    })
  }

  const onCancel = () => {
    reset(freshDefaults())
    onClose()
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onCancel()
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add User</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
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
              />
              {errors.email && (
                <p className="text-xs text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                {...register("name")}
                placeholder="Full name"
                type="text"
              />
              {errors.name && (
                <p className="text-xs text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Set Password</Label>
              <Input
                id="password"
                {...register("password", {
                  required: "Password is required",
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                })}
                placeholder="Password"
                type="password"
              />
              {errors.password && (
                <p className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="confirm_password">Confirm Password</Label>
              <Input
                id="confirm_password"
                {...register("confirm_password", {
                  required: "Please confirm your password",
                  validate: (value) =>
                    value === getValues().password ||
                    "The passwords do not match",
                })}
                placeholder="Password"
                type="password"
              />
              {errors.confirm_password && (
                <p className="text-xs text-destructive">
                  {errors.confirm_password.message}
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={onCancel} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddUser
