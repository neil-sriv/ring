import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
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
import { Card, CardContent } from "@/components/ui/card"
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

  return (
    <div className="w-full">
      <div className="flex flex-col gap-6">
        <h3 className="text-sm font-semibold text-foreground">
          User Information
        </h3>
        <Card className="w-full md:w-1/2">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full name</Label>
                {editMode ? (
                  <Input
                    id="name"
                    {...register("name", { maxLength: 30 })}
                    type="text"
                  />
                ) : (
                  <p
                    className={`py-2 ${
                      !currentUser?.name
                        ? "text-muted-foreground"
                        : "text-foreground"
                    }`}
                  >
                    {currentUser?.name || "N/A"}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
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
                  <p className="py-2 text-foreground">{currentUser?.email}</p>
                )}
                {errors.email && (
                  <p className="text-sm text-destructive">
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
                    {isSubmitting && (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    )}
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
          </CardContent>
        </Card>
        <div>
          <Button
            variant="outline"
            onClick={() => {
              subscribeToPush(currentUser!.api_identifier)
            }}
          >
            Enable Notifications
          </Button>
        </div>
      </div>
    </div>
  )
}

export default UserInformation
