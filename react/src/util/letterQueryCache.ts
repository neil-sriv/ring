import type { PublicLetter } from "../client"

/**
 * Match cached letter-detail queries that belong to a given group.
 * Used after membership changes, which update in-progress/upcoming
 * letter participants on the server.
 */
export function isGroupLetterDetailQuery(
  queryKey: readonly unknown[],
  groupApiId: string,
  data: unknown,
): boolean {
  const first = queryKey[0]
  if (
    typeof first !== "object" ||
    first === null ||
    !("_id" in first) ||
    (first as { _id: string })._id !== "readLetterLettersLetterLetterApiIdGet"
  ) {
    return false
  }
  const letter = data as PublicLetter | undefined
  return letter?.group?.api_identifier === groupApiId
}
