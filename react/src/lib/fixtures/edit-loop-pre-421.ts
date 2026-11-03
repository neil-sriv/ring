export const EDIT_LOOP_PRE_421_SHA = "f0d0533"
export const EDIT_LOOP_PRE_421_PARENT = "f0d0533^"
export const EDIT_LOOP_PRE_421_PR = 421

export const EDIT_LOOP_PRE_421_SOURCE = `
  const mutation = useMutation({
    ...editLetterLettersLetterLetterApiIdEditLetterPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Letter updated successfully.", "success")
      reset()
      onClose()
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
          path: { letter_api_id: loop.api_identifier },
        }),
      })
    },
  })
`
