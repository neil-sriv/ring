import { readFileSync } from "node:fs"

import { EDIT_LOOP_PRE_421_SOURCE } from "./fixtures/edit-loop-pre-421.ts"
import {
  type MutationCacheId,
  invalidatedQueryIds,
  missingPolicyQueryIds,
} from "./queryCachePolicy.ts"

function failPastEditLoop(): number {
  const missing = missingPolicyQueryIds(
    "editLetter",
    invalidatedQueryIds(EDIT_LOOP_PRE_421_SOURCE),
  )
  if (missing.length === 0) {
    console.error(
      "query-cache prove: reconstructed f0d0533^ EditLoop unexpectedly covers editLetter",
    )
    return 1
  }
  console.error(
    `query-cache policy editLetter rejected f0d0533^ (#421) EditLoop; missing ${missing.join(
      ", ",
    )}`,
  )
  return 1
}

function checkSource(path: string, cache: string): number {
  const source = readFileSync(path, "utf8")
  const missing = missingPolicyQueryIds(
    cache as MutationCacheId,
    invalidatedQueryIds(source),
  )
  if (missing.length > 0) {
    console.error(
      `query-cache policy ${cache} rejected ${path}; missing ${missing.join(
        ", ",
      )}`,
    )
    return 1
  }
  return 0
}

const args = process.argv.slice(2)
if (args[0] === "--prove") {
  process.exit(failPastEditLoop())
}

if (args.length === 2) {
  process.exit(checkSource(args[0], args[1]))
}

console.error("usage: checkQueryCache.ts --prove | <source> <mutationCacheId>")
process.exit(2)
