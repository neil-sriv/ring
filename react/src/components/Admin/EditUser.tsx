import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  UpdateUserByIdPartiesUserUserApiIdPatchError,
  UserLinked,
  UserUpdate,
} from "../../client"
import {
  readUsersPartiesUsersGetQueryKey,
  updateUserByIdPartiesUserUserApiIdPatchMutation,
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

interface EditUserProps {
  user: UserLinked
  isOpen: boolean
  onClose: () => void
}

const EditUser = ({ user, isOpen, onClose }: EditUserProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<UserUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: user.email,
      name: user.name ?? "",
    },
  })

  useEffect(() => {
    if (isOpen) {
      reset({
        email: user.email,
        name: user.name ?? "",
      })
    }
  }, [isOpen, user.email, user.name, reset])

  const mutation = useMutation({
    ...updateUserByIdPartiesUserUserApiIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "User updated successfully.", "success")
      reset()
      onClose()
    },
    onError: (
      error: AxiosError<UpdateUserByIdPartiesUserUserApiIdPatchError>,
    ) => {
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

  const onSubmit: SubmitHandler<UserUpdate> = (data) => {
    mutation.mutate({
      path: { user_api_id: user.api_identifier },
      body: {
        email: data.email,
        name: data.name,
      },
    })
  }

  const onCancel = () => {
    reset()
    onClose()
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
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
              <Input id="name" {...register("name")} type="text" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={onCancel} type="button">
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !isDirty}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default EditUser
