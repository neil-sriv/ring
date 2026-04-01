import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { UserLinked, UserUpdate } from "../../client"
import {
  readUsersPartiesUsersGetQueryKey,
  updateUserPartiesUserIdPatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { emailPattern } from "../../util/misc"

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

interface UserUpdateForm extends UserUpdate {
  confirm_password: string
}

const EditUser = ({ user, isOpen, onClose }: EditUserProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<UserUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: user,
  })

  const mutation = useMutation({
    ...updateUserPartiesUserIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "User updated successfully.", "success")
      reset()
      onClose()
    },
    // onError: (err: AxiosError<UpdateUserMePartiesMePatchError>) => {
    //   const errDetail =
    //     err.response?.data.detail || "no error detail, please contact support";
    //   showToast("Something went wrong.", `${errDetail}`, "error");
    // },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserUpdateForm> = async () => {
    mutation.mutate({})
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
          <div className="py-4 space-y-4">
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
              />
              {errors.email && (
                <p className="text-sm text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" {...register("name")} type="text" />
            </div>
            {/* <div className="space-y-2">
              <Label htmlFor="password">Set Password</Label>
              <Input
                id="password"
                {...register("password", {
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                })}
                placeholder="Password"
                type="password"
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              )}
            </div> */}
            {/* <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm Password</Label>
              <Input
                id="confirm_password"
                {...register("confirm_password", {
                  validate: (value) =>
                    value === getValues().password ||
                    "The passwords do not match",
                })}
                placeholder="Password"
                type="password"
              />
              {errors.confirm_password && (
                <p className="text-sm text-destructive">
                  {errors.confirm_password.message}
                </p>
              )}
            </div> */}
            <div className="flex gap-4">
              <div>
                {/* <Checkbox {...register("is_superuser")} colorScheme="teal">
                  Is superuser?
                </Checkbox> */}
              </div>
              <div>
                {/* <Checkbox {...register("is_active")} colorScheme="teal">
                  Is active?
                </Checkbox> */}
              </div>
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
