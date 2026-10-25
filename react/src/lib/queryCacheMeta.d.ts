import type { MutationCacheId } from "./queryCachePolicy"

declare module "@tanstack/react-query" {
  interface Register {
    mutationMeta: {
      cache?: MutationCacheId
    }
  }
}
