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
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
    onSuccess: async (data: Token) => {
      showToast("Success!", "Impersonated user successfully.", "success")
      reset()
      onClose()
      localStorage.setItem("access_token", data.access_token)
      // Soft SPA navigations keep the QueryClient alive with the admin's /me
      // and dashboard still warm (30s staleTime). Refetch /me in place so
      // mounted shell observers (App/Layout/Sidebar/UserMenu) stay subscribed
      // — removeQueries()/clear() on /me orphans those observers with stale
      // React state. Then drop every other cached query for the prior identity.
      // Login can clear() because the shell is not mounted on /login.
      // staleTime: 0 forces a network refetch; otherwise fetchQuery returns the
      // still-fresh admin /me from the default 30s cache.
      await queryClient.cancelQueries()
      await queryClient.fetchQuery({
        ...readUserMePartiesMeGetOptions(),
        staleTime: 0,
      })
      queryClient.removeQueries({
        predicate: (query) => {
          const head = query.queryKey[0] as { _id?: string } | undefined
          return head?._id !== "readUserMePartiesMeGet"
        },
      })
      navigate({ to: "/" })
    },
    onError: (
      err: AxiosError<ImpersonateUserTokenImpersonateUserTokenPostError>,
    ) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
  })

  const onSubmit: SubmitHandler<UserImpersonateForm> = async () => {
    await mutation.mutateAsync({
      query: {
        user_api_id: user.api_identifier,
      },
    })
  }

  const onCancel = () => {
    reset()
    onClose()
  }

  const isSaving = isSubmitting || mutation.isPending

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open && !isSaving) {
          reset()
          onClose()
        }
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Impersonate User</DialogTitle>
            <DialogDescription>
              You will be signed in as this user until you log out.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="id">User ID</Label>
              <Input
                id="id"
                {...register("id", {
                  required: "User ID is required",
                })}
                placeholder="User ID"
                type="text"
                disabled={isSaving}
              />
              {errors.id && (
                <p className="text-xs text-destructive">{errors.id.message}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={onCancel}
              type="button"
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button variant="destructive" type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
              Impersonate
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default ImpersonateUser
