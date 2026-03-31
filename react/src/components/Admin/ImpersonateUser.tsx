import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { useNavigate } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import type {
  ImpersonateUserTokenImpersonateUserTokenPostError,
  Token,
  UserLinked,
} from "../../client"
import {
  impersonateUserTokenImpersonateUserTokenPostMutation,
  readUserMePartiesMeGetOptions,
  readUsersPartiesUsersGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"

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

interface ImpersonateUserProps {
  user: UserLinked
  isOpen: boolean
  onClose: () => void
}

interface UserImpersonateForm {
  id: string
}

const ImpersonateUser = ({ user, isOpen, onClose }: ImpersonateUserProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserImpersonateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      id: user.api_identifier,
    },
  })

  const mutation = useMutation({
    ...impersonateUserTokenImpersonateUserTokenPostMutation(),
    onSuccess: (data: Token) => {
      showToast("Success!", "Impersonated user successfully.", "success")
      reset()
      onClose()
      localStorage.setItem("access_token", data.access_token)
      queryClient.invalidateQueries()
      queryClient.ensureQueryData({
        ...readUserMePartiesMeGetOptions({}),
      })
      navigate({ to: "/" })
    },
    onError: (
      err: AxiosError<ImpersonateUserTokenImpersonateUserTokenPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserImpersonateForm> = async () => {
    mutation.mutate({
      query: {
        user_api_id: user.api_identifier,
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
            <DialogTitle>Impersonate User</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="id">User ID</Label>
              <Input
                id="id"
                {...register("id", {
                  required: "User ID is required",
                })}
                placeholder="User ID"
                type="text"
              />
              {errors.id && (
                <p className="text-sm text-destructive">{errors.id.message}</p>
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

export default ImpersonateUser
