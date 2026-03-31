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

type QuestionField = {
  question_text: string
}

type FormData = {
  questions: QuestionField[]
  cycle_length: number
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

  const defaultQuestionsMutation = useMutation({
    ...replaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Loop settings updated successfully.", "success")
    },
    onError: (
      err: AxiosError<ReplaceGroupDefaultQuestionsPartiesGroupGroupApiIdReplaceDefaultQuestionsPostError>,
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: async () => {
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
    },
  })

  const cycleUpdateMutation = useMutation({
    ...updateGroupPartiesGroupGroupApiIdPatchMutation(),
    onSuccess: () => {
      showToast("Success!", "Cycle length updated successfully.", "success")
    },
    onError: (err: AxiosError<UpdateGroupPartiesGroupGroupApiIdPatchError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support"
      showToast("Something went wrong.", `${errDetail}`, "error")
    },
    onSettled: async () => {
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
    },
  })

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    if (data.cycle_length !== group.cycle_length) {
      cycleUpdateMutation.mutate({
        body: { cycle_length: data.cycle_length },
        path: { group_api_id: groupId },
      })
    }

    defaultQuestionsMutation.mutate({
      body: {
        questions: data.questions.map((question) => question.question_text),
      },
      path: { group_api_id: groupId },
    })

    toggleEditMode()
  }

  const onCancel = () => {
    reset()
    toggleEditMode()
  }

  return (
    <>
      <div className="w-full">
        <h3 className="text-sm font-semibold py-4">Loop Settings</h3>
        <div className="w-full md:w-1/2">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1">
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
                <p className="py-2 text-foreground">
                  {group.cycle_length} days
                </p>
              )}
              {errors.cycle_length && (
                <p className="text-sm text-destructive">
                  {errors.cycle_length.message}
                </p>
              )}
            </div>
            <div className="mt-4 space-y-1">
              <Label htmlFor="defaultQuestions">Default Questions</Label>
              <ul className="space-y-2">
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
                                {...register(
                                  `questions.${index}.question_text`,
                                )}
                                {...field}
                              />
                            )}
                          />
                          <Button
                            type="button"
                            onClick={() => remove(index)}
                            size="sm"
                            variant="outline"
                          >
                            Remove
                          </Button>
                        </>
                      ) : (
                        <p className="py-2 text-foreground">
                          {field.question_text}
                        </p>
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
                    </Button>
                  </li>
                )}
                {errors.questions?.root && (
                  <li>
                    <p className="text-sm text-destructive">
                      {errors.questions.root?.message}
                    </p>
                  </li>
                )}
              </ul>
            </div>
            <div className="flex mt-4 gap-3">
              <Button
                onClick={editMode ? undefined : toggleEditMode}
                type={editMode ? "submit" : "button"}
                disabled={editMode ? !isDirty || isSubmitting : false}
              >
                {editMode && isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {editMode ? "Save" : "Edit"}
              </Button>
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
        </div>
      </div>
    </>
  )
}

export default GroupLoopSettings
