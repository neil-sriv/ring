import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import { toast } from "sonner"
import type {
  UpdateUserMePartiesMePatchError,
  UserLinked,
  UserUpdate,
} from "../../client"
import {
  readUserMePartiesMeGetQueryKey,
  readUsersPartiesUsersGetQueryKey,
  updateUserMePartiesMePatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { emailPattern, formatApiErrorDetail } from "../../util/misc"
import { subscribeToPush } from "../../util/notifications"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const UserInformation = () => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<UserLinked>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: currentUser?.name,
      email: currentUser?.email,
    },
  })

  const mutation = useMutation({
    ...updateUserMePartiesMePatchMutation(),
    onSuccess: (_data, variables) => {
      showToast("Success!", "User updated successfully.", "success")
      setEditMode(false)
      reset({
        name: variables.body?.name ?? currentUser?.name,
        email: variables.body?.email ?? currentUser?.email,
      })
    },
    onError: (err: AxiosError<UpdateUserMePartiesMePatchError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: async () => {
      queryClient.invalidateQueries({
        queryKey: readUsersPartiesUsersGetQueryKey(),
      })
      await queryClient.refetchQueries({
        queryKey: readUserMePartiesMeGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserUpdate> = async (data) => {
    mutation.mutate({ body: data })
  }

  const onCancel = () => {
    reset()
    setEditMode(false)
  }

  const [isEnablingNotifications, setIsEnablingNotifications] = useState(false)
  const [notificationFeedback, setNotificationFeedback] = useState<{
    tone: "success" | "error"
    message: string
  } | null>(null)

  const handleEnableNotifications = async () => {
    if (!currentUser?.api_identifier || isEnablingNotifications) {
      return
    }
    setIsEnablingNotifications(true)
    setNotificationFeedback(null)
    try {
      const result = await subscribeToPush(currentUser.api_identifier)
      if (result.ok) {
        const message = "Push notifications are enabled for this browser."
        setNotificationFeedback({ tone: "success", message })
        toast.success("Success!", {
          id: "enable-notifications",
          description: message,
          duration: 8000,
        })
        return
      }
      setNotificationFeedback({ tone: "error", message: result.message })
      toast.error("Couldn't enable notifications", {
        id: "enable-notifications",
        description: result.message,
        duration: 8000,
      })
    } finally {
      setIsEnablingNotifications(false)
    }
  }

  return (
    <div className="flex w-full flex-col gap-10">
      <section>
        <h3 className="text-base font-semibold">My profile</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Your name and email, as other members see them.
        </p>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-5 flex max-w-md flex-col gap-5"
        >
          <div className="flex flex-col gap-1.5">
            <Label
              htmlFor="name"
              className={editMode ? undefined : "text-muted-foreground"}
            >
              Full name
            </Label>
            {editMode ? (
              <Input
                id="name"
                {...register("name", { maxLength: 30 })}
                type="text"
              />
            ) : (
              <p
                className={`text-sm ${
                  !currentUser?.name
                    ? "text-muted-foreground"
                    : "text-foreground"
                }`}
              >
                {currentUser?.name || "N/A"}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label
              htmlFor="email"
              className={editMode ? undefined : "text-muted-foreground"}
            >
              Email
            </Label>
            {editMode ? (
              <Input
                id="email"
                {...register("email", {
                  required: "Email is required",
                  pattern: emailPattern,
                })}
                type="email"
              />
            ) : (
              <p className="text-sm text-foreground">{currentUser?.email}</p>
            )}
            {errors.email && (
              <p className="text-xs text-destructive">
                {errors.email.message}
              </p>
            )}
          </div>
          <div className="flex gap-3">
            {editMode ? (
              <Button
                type="submit"
                disabled={isSubmitting || !isDirty || !getValues("email")}
              >
                {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                Save
              </Button>
            ) : (
              <Button type="button" onClick={() => setEditMode(true)}>
                Edit
              </Button>
            )}
            {editMode && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </section>
      <section>
        <h3 className="text-base font-semibold">Notifications</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Get a push notification in this browser when something new arrives.
        </p>
        <div className="mt-5 flex flex-col gap-1.5">
          <div>
            <Button
              variant="outline"
              type="button"
              disabled={isEnablingNotifications}
              onClick={() => {
                void handleEnableNotifications()
              }}
            >
              {isEnablingNotifications && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Enable notifications
            </Button>
          </div>
          {notificationFeedback && (
            <p
              role="status"
              aria-live="polite"
              className={
                notificationFeedback.tone === "error"
                  ? "max-w-md text-sm text-destructive"
                  : "max-w-md text-sm text-muted-foreground"
              }
            >
              {notificationFeedback.tone === "error"
                ? `Couldn't enable notifications: ${notificationFeedback.message}`
                : notificationFeedback.message}
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

export default UserInformation
