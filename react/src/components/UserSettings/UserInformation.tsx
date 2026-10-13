import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
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
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listGroupsPartiesGroupsGetQueryKey,
  readUserMePartiesMeGetOptions,
  readUserMePartiesMeGetQueryKey,
  readUsersPartiesUsersGetQueryKey,
  updateUserMePartiesMePatchMutation,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { emailPattern, formatApiErrorDetail } from "../../util/misc"

import { PushNotificationSettings } from "@/components/Common/PushOffer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const UserInformation = () => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  // Subscribe so view-mode name/email update when /me refetches after save.
  // getQueryData alone would leave the page stuck on the pre-save values.
  const { data: currentUser } = useQuery({
    ...readUserMePartiesMeGetOptions(),
  })
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
      // Groups list / membership / Home Facepile embed member names from
      // list queries with a 30s staleTime. Refetching /me alone leaves those
      // nested names stale on soft-nav until the cache expires.
      if (currentUser?.api_identifier) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser.api_identifier },
          }),
        })
      }
      queryClient.invalidateQueries({
        queryKey: [{ _id: "readGroupPartiesGroupGroupApiIdGet" }],
      })
      queryClient.invalidateQueries({
        queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
      })
      queryClient.invalidateQueries({
        queryKey: [{ _id: "readLetterLettersLetterLetterApiIdGet" }],
      })
      await queryClient.refetchQueries({
        queryKey: readUserMePartiesMeGetQueryKey(),
      })
    },
  })

  const onSubmit: SubmitHandler<UserUpdate> = async (data) => {
    await mutation.mutateAsync({ body: data })
  }

  const syncFormFromCurrentUser = () => {
    const latest = queryClient.getQueryData<UserLinked>(
      readUserMePartiesMeGetQueryKey(),
    )
    reset({
      name: latest?.name,
      email: latest?.email,
    })
  }

  const onEdit = () => {
    // defaultValues are from mount — re-sync so Edit shows the latest /me cache
    syncFormFromCurrentUser()
    setEditMode(true)
  }

  const onCancel = () => {
    syncFormFromCurrentUser()
    setEditMode(false)
  }

  const isSaving = isSubmitting || mutation.isPending

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
                disabled={isSaving}
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
                disabled={isSaving}
              />
            ) : (
              <p className="text-sm text-foreground">{currentUser?.email}</p>
            )}
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>
          <div className="flex gap-3">
            {editMode ? (
              <Button
                type="submit"
                disabled={isSaving || !isDirty || !getValues("email")}
              >
                {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
                Save
              </Button>
            ) : (
              <Button type="button" onClick={onEdit}>
                Edit
              </Button>
            )}
            {editMode && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isSaving}
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </section>
      <PushNotificationSettings userApiId={currentUser?.api_identifier} />
    </div>
  )
}

export default UserInformation
