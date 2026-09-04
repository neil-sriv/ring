import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import {
  Controller,
  type SubmitHandler,
  useFieldArray,
  useForm,
} from "react-hook-form"

import { useRouter } from "@tanstack/react-router"
import type { AxiosError } from "axios"
import { Loader2, Plus } from "lucide-react"
import type { GroupLinked } from "../../client"
import {
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation,
  updateGroupPartiesGroupGroupApiIdPatchMutation,
} from "../../client/@tanstack/react-query.gen"
import type {
  ReplaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostError,
  UpdateGroupPartiesGroupGroupApiIdPatchError,
} from "../../client/types.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

type QuestionField = {
  question_text: string
}

type FormData = {
  questions: QuestionField[]
  cycle_length: number
  min_responder_percent: number
}

const DEFAULT_MIN_RESPONDER_PERCENT = 50

function displayMinResponderPercent(ratio: number | null | undefined): number {
  if (ratio == null) {
    return DEFAULT_MIN_RESPONDER_PERCENT
  }
  return Math.round(ratio * 100)
}

function GroupLoopSettings({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    }),
  )

  if (group === undefined) {
    return null
  }

  const router = useRouter()
  const {
    handleSubmit,
    reset,
    control,
    register,
    formState: { isSubmitting, isDirty, errors },
  } = useForm<FormData>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      questions: group.default_questions.map((question) => ({
        question_text: question.question_text,
      })),
      cycle_length: group.cycle_length,
      min_responder_percent: displayMinResponderPercent(
        group.min_responder_ratio,
      ),
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "questions",
    rules: {
      validate: (value) =>
        value.every((question) => question.question_text.length > 0) ||
        "Question cannot be empty.",
    },
  })

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const refreshGroup = async () => {
    queryClient.invalidateQueries({
      queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: groupId },
      }),
    })
    router.invalidate()
    await queryClient.refetchQueries({
      queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
        path: { group_api_id: groupId },
      }),
    })
  }

  const defaultQuestionsMutation = useMutation({
    ...replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation(),
  })

  const cycleUpdateMutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
  })

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    const currentMinResponderPercent = displayMinResponderPercent(
      group.min_responder_ratio,
    )
    const groupPatch: {
      cycle_length?: number
      min_responder_ratio?: number
    } = {}
    if (data.cycle_length !== group.cycle_length) {
      groupPatch.cycle_length = data.cycle_length
    }
    if (data.min_responder_percent !== currentMinResponderPercent) {
      groupPatch.min_responder_ratio = data.min_responder_percent / 100
    }

    try {
      // Apply default questions first so a questions failure cannot leave
      // cycle / min_responder changes applied alone.
      await defaultQuestionsMutation.mutateAsync({
        body: {
          questions: data.questions.map((question) => question.question_text),
        },
        path: { group_api_id: groupId },
      })

      if (Object.keys(groupPatch).length > 0) {
        try {
          await cycleUpdateMutation.mutateAsync({
            body: groupPatch,
            path: { group_api_id: groupId },
          })
        } catch (cycleErr) {
          const axiosErr =
            cycleErr as AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>
          showToast(
            "Partially saved.",
            `Default questions were updated, but cycle settings could not be saved. ${formatApiErrorDetail(
              axiosErr.response?.data?.detail,
            )}`,
            "error",
          )
          return
        }
      }

      showToast("Success!", "Loop settings updated successfully.", "success")
      setEditMode(false)
    } catch (err) {
      const axiosErr = err as AxiosError<
        | ReplaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostError
        | UpdateGroupPartiesGroupGroupApiIdPatchError
      >
      showToast(
        "Something went wrong.",
        formatApiErrorDetail(axiosErr.response?.data?.detail),
        "error",
      )
    } finally {
      await refreshGroup()
    }
  }

  const onCancel = () => {
    reset()
    toggleEditMode()
  }

  return (
    <div className="w-full max-w-xl">
      <h3 className="text-base font-semibold">Loop Settings</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        How often this group's loop runs and the questions each issue starts
        with.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6">
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cycle_length">Loop Cycle (days)</Label>
            {editMode ? (
              <Input
                id="cycle_length"
                {...register("cycle_length", {
                  valueAsNumber: true,
                  required: "Cycle length is required",
                  min: {
                    value: 1,
                    message: "Cycle length must be greater than 0",
                  },
                })}
                type="number"
              />
            ) : (
              <p className="text-sm">{group.cycle_length} days</p>
            )}
            {errors.cycle_length && (
              <p className="text-xs text-destructive">
                {errors.cycle_length.message}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="min_responder_percent">
              Minimum responses before send
            </Label>
            {editMode ? (
              <Input
                id="min_responder_percent"
                {...register("min_responder_percent", {
                  valueAsNumber: true,
                  required: "Minimum response percentage is required",
                  min: {
                    value: 0,
                    message: "Percentage must be at least 0",
                  },
                  max: {
                    value: 100,
                    message: "Percentage must be at most 100",
                  },
                })}
                type="number"
                step={5}
              />
            ) : (
              <p className="text-sm">
                {displayMinResponderPercent(group.min_responder_ratio)}%
                {group.min_responder_ratio === 0 ? " (disabled)" : ""}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              If not enough members have responded by the send date, the issue
              is delayed by one day and retried. Set to 0% to send on schedule
              regardless of responses.
            </p>
            {errors.min_responder_percent && (
              <p className="text-xs text-destructive">
                {errors.min_responder_percent.message}
              </p>
            )}
          </div>
        </div>
        <div className="mt-6 border-t pt-6">
          <h4 className="text-base font-semibold">Default Questions</h4>
          <p className="mt-1 text-sm text-muted-foreground">
            Every new loop starts with these questions.
          </p>
          <ul className="mt-4 flex flex-col gap-2">
            {fields.map((field, index) => (
              <li key={field.id}>
                <div className="flex gap-2">
                  {editMode ? (
                    <>
                      <Controller
                        control={control}
                        name={`questions.${index}.question_text`}
                        render={({ field }) => (
                          <Input
                            {...register(`questions.${index}.question_text`)}
                            {...field}
                          />
                        )}
                      />
                      <Button
                        type="button"
                        onClick={() => remove(index)}
                        size="sm"
                        variant="ghost"
                        className="text-muted-foreground hover:text-destructive"
                      >
                        Remove
                      </Button>
                    </>
                  ) : (
                    <p className="text-sm">{field.question_text}</p>
                  )}
                </div>
              </li>
            ))}
            {editMode && (
              <li>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => append({ question_text: "" })}
                >
                  <Plus className="h-4 w-4" />
                  Add question
                </Button>
              </li>
            )}
            {errors.questions?.root && (
              <li>
                <p className="text-xs text-destructive">
                  {errors.questions.root?.message}
                </p>
              </li>
            )}
          </ul>
        </div>
        <div className="mt-6 flex gap-3 border-t pt-6">
          <Button
            onClick={editMode ? undefined : toggleEditMode}
            type={editMode ? "submit" : "button"}
            disabled={
              editMode
                ? !isDirty ||
                  isSubmitting ||
                  cycleUpdateMutation.isPending ||
                  defaultQuestionsMutation.isPending
                : false
            }
          >
            {editMode &&
              (isSubmitting ||
                cycleUpdateMutation.isPending ||
                defaultQuestionsMutation.isPending) && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
            {editMode ? "Save" : "Edit"}
          </Button>
          {editMode && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={
                isSubmitting ||
                cycleUpdateMutation.isPending ||
                defaultQuestionsMutation.isPending
              }
            >
              Cancel
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}

export default GroupLoopSettings
