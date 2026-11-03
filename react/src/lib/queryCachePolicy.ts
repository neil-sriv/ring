import type { QueryClient, QueryKey } from "@tanstack/react-query"

export const CACHE_SURFACES = {
  letter: "readLetterLettersLetterLetterApiIdGet",
  letters: "listLettersLettersLettersGet",
  dashboard: "listDashboardLettersLettersLettersDashboardGet",
  me: "readUserMePartiesMeGet",
  group: "readGroupPartiesGroupGroupApiIdGet",
  documents: "listDocumentsNotebookDocumentsGet",
  document: "getDocumentEndpointNotebookDocumentsDocumentApiIdGet",
} as const

export type CacheSurface = keyof typeof CACHE_SURFACES

export const MUTATION_CACHE_POLICY = {
  editLetter: ["letter", "letters", "dashboard"],
  addLetter: ["letters", "dashboard"],
  updateMe: ["me"],
  updateDocument: ["document", "documents"],
} as const satisfies Record<string, readonly CacheSurface[]>

export type MutationCacheId = keyof typeof MUTATION_CACHE_POLICY

export function policyQueryIds(cache: MutationCacheId): string[] {
  return MUTATION_CACHE_POLICY[cache].map((surface) => CACHE_SURFACES[surface])
}

const QUERY_KEY_CALL = /(\w+)QueryKey\s*\(/g

export function invalidatedQueryIds(source: string): string[] {
  const ids = new Set<string>()
  for (const match of source.matchAll(QUERY_KEY_CALL)) {
    ids.add(match[1])
  }
  return [...ids]
}

export function missingPolicyQueryIds(
  cache: MutationCacheId,
  invalidatedIds: readonly string[],
): string[] {
  const have = new Set(invalidatedIds)
  return policyQueryIds(cache).filter((id) => !have.has(id))
}

function queryHeadId(queryKey: QueryKey): string | undefined {
  const head = queryKey[0]
  if (typeof head !== "object" || head === null || !("_id" in head)) {
    return undefined
  }
  const id = (head as { _id: unknown })._id
  return typeof id === "string" ? id : undefined
}

export function applyMutationCachePolicy(
  queryClient: QueryClient,
  cache: MutationCacheId,
): void {
  const ids = new Set(policyQueryIds(cache))
  void queryClient.invalidateQueries({
    predicate: (query) => {
      const id = queryHeadId(query.queryKey)
      return id !== undefined && ids.has(id)
    },
  })
}
