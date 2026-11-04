import { useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import {
  type PublicLetter,
  reorderQuestionsLettersLetterLetterApiIdReorderQuestionsPost,
} from "../../client"
import {
  listDashboardLettersLettersLettersDashboardGetQueryKey,
  readLetterLettersLetterLetterApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { useSubmitOnce } from "../../hooks/useSubmitOnce"
import { formatApiErrorDetail } from "../../util/misc"
import {
  movedQuestionIds,
  withQuestionPositions,
} from "../../util/questionOrder"

export function useReorderLetterQuestions(loopApiId: string) {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const submitOnce = useSubmitOnce()
  const letterQueryKey = readLetterLettersLetterLetterApiIdGetQueryKey({
    path: { letter_api_id: loopApiId },
  })

  const move = (
    orderedIds: readonly string[],
    index: number,
    delta: -1 | 1,
  ) => {
    const nextIds = movedQuestionIds(orderedIds, index, delta)
    if (!nextIds) {
      return
    }
    void submitOnce.run(async () => {
      await queryClient.cancelQueries({ queryKey: letterQueryKey })
      const previous = queryClient.getQueryData<PublicLetter>(letterQueryKey)
      queryClient.setQueryData<PublicLetter>(letterQueryKey, (current) => {
        if (!current) {
          return current
        }
        const currentIds = new Set(
          current.questions.map((question) => question.api_identifier),
        )
        if (
          currentIds.size !== nextIds.length ||
          nextIds.some((id) => !currentIds.has(id))
        ) {
          return current
        }
        return {
          ...current,
          questions: withQuestionPositions(current.questions, nextIds),
        }
      })
      try {
        const { data } =
          await reorderQuestionsLettersLetterLetterApiIdReorderQuestionsPost({
            path: { letter_api_id: loopApiId },
            body: { question_api_identifiers: nextIds },
            throwOnError: true,
          })
        queryClient.setQueryData(letterQueryKey, data)
        queryClient.invalidateQueries({
          queryKey: listDashboardLettersLettersLettersDashboardGetQueryKey(),
        })
      } catch (error) {
        if (previous) {
          queryClient.setQueryData(letterQueryKey, previous)
        }
        const axiosError = error as AxiosError<{ detail?: unknown }>
        showToast(
          "Couldn't reorder questions",
          formatApiErrorDetail(axiosError.response?.data?.detail),
          "error",
        )
      }
    })
  }

  return { pending: submitOnce.pending, move }
}
