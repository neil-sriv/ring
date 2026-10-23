import { MutationCache, QueryClient } from "@tanstack/react-query"

import { applyMutationCachePolicy } from "./queryCachePolicy"

export function createAppQueryClient(): QueryClient {
  const queryClient = new QueryClient({
    mutationCache: new MutationCache({
      onSettled: (_data, _error, _variables, _context, mutation) => {
        const cache = mutation.meta?.cache
        if (cache) {
          applyMutationCachePolicy(queryClient, cache)
        }
      },
    }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: true,
      },
    },
  })
  return queryClient
}
