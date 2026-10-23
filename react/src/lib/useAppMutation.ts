import { type UseMutationOptions, useMutation } from "@tanstack/react-query"

import type { MutationCacheId } from "./queryCachePolicy"

export function useAppMutation<
  TData = unknown,
  TError = Error,
  TVariables = void,
  TOnMutateResult = unknown,
>(
  options: UseMutationOptions<TData, TError, TVariables, TOnMutateResult> & {
    cache: MutationCacheId
  },
) {
  const { cache, meta, ...rest } = options
  return useMutation({
    ...rest,
    meta: { ...meta, cache },
  })
}
