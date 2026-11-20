import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { AxiosError } from "axios"
import type {
  CreateGroupPartiesGroupPostError,
  GroupCreate,
} from "../../client"
import {
  createGroupPartiesGroupPostMutation,
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  listGroupsPartiesGroupsGetQueryKey,
  readUserMePartiesMeGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { useSubmitOnce } from "../../hooks/useSubmitOnce"
import { formatApiErrorDetail } from "../../util/misc"

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

// Axios leaves timeout at 0, so a hung create never rejects and isSaving stays
// true. This write is a small JSON body; uploads keep the longer proxy window.
const CREATE_GROUP_TIMEOUT_MS = 20_000

interface AddGroupProps {
  isOpen: boolean
  onClose: () => void
}

const AddGroup = ({ isOpen, onClose }: AddGroupProps) => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  // Subscribe so create uses the live /me identity (admin_api_identifier +
  // listGroups invalidation key). getQueryData alone never re-renders when
  // /me is rewritten in cache (e.g. after impersonation while this dialog
  // stays mounted under Navbar on /groups).
  const { data: currentUser } = useQuery({
    ...readUserMePartiesMeGetOptions(),
  })
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GroupCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
    },
  })

  // Parent keeps this dialog mounted; clear name each open.
  useEffect(() => {
    if (isOpen) {
      reset(
        { name: "" },
        { keepErrors: false, keepDirty: false, keepTouched: false },
      )
    }
  }, [isOpen, reset])

  const mutation = useMutation({
    ...createGroupPartiesGroupPostMutation(),
    onSuccess: (group) => {
      showToast("Success!", "Group created successfully.", "success")
      reset({ name: "" })
      onClose()
      // Same post-create handoff as Add Loop / New Document: land on the new
      // resource instead of leaving the user on a stale Groups/Home list.
      void navigate({
        to: "/groups/$groupId/loops",
        params: { groupId: group.api_identifier },
      })
    },
    onError: (err: AxiosError<CreateGroupPartiesGroupPostError>) => {
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
    },
    onSettled: (data) => {
      if (data && currentUser) {
        queryClient.invalidateQueries({
          queryKey: listGroupsPartiesGroupsGetQueryKey({
            query: { user_api_id: currentUser.api_identifier },
          }),
        })
        queryClient.invalidateQueries({
          queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
        })
        queryClient.invalidateQueries({
          queryKey: readUserMePartiesMeGetQueryKey(),
        })
      }
    },
  })

  const submitOnce = useSubmitOnce()
  const isSaving = isSubmitting || mutation.isPending || submitOnce.pending

  const onSubmit: SubmitHandler<GroupCreate> = async (data) => {
    if (!currentUser) {
      return
    }
    await submitOnce.run(async () => {
      try {
        await mutation.mutateAsync({
          body: {
            admin_api_identifier: currentUser.api_identifier,
            name: data.name,
          },
          timeout: CREATE_GROUP_TIMEOUT_MS,
        })
      } catch {
        // onError already toasts. Swallow so handleSubmit clears isSubmitting
        // and the dialog stays open for retry / Cancel.
      }
    })
  }

  const onCancel = () => {
    reset({ name: "" })
    onClose()
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open && !isSaving) onCancel()
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add Group</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-5 py-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                {...register("name", {
                  required: "Name is required.",
                })}
                placeholder="Name"
                type="text"
                disabled={isSaving || !currentUser}
              />
              {errors.name && (
                <p className="text-xs text-destructive">
                  {errors.name.message}
                </p>
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
            <Button type="submit" disabled={isSaving || !currentUser}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default AddGroup
