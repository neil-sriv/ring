import { readFileSync } from "node:fs"

import { EDIT_LOOP_PRE_421_SOURCE } from "./fixtures/edit-loop-pre-421.ts"
import {
  MUTATION_CACHE_POLICY,
  type MutationCacheId,
  invalidatedQueryIds,
  missingPolicyQueryIds,
} from "./queryCachePolicy.ts"

function isMutationCacheId(cache: string): cache is MutationCacheId {
  return cache in MUTATION_CACHE_POLICY
}

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
  console.log(
    `query-cache policy editLetter rejected f0d0533^ (#421) EditLoop; missing ${missing.join(
      ", ",
    )}`,
  )
  return 0
}

function checkSource(path: string, cache: string): number {
  if (!isMutationCacheId(cache)) {
    console.error(`unknown mutation cache id: ${cache}`)
    return 1
  }
  const source = readFileSync(path, "utf8")
  const cacheDecl = new RegExp(`cache:\\s*["']${cache}["']`)
  if (!cacheDecl.test(source)) {
    console.error(`${path} does not declare cache: "${cache}"`)
    return 1
  }
  if (source.includes("invalidateQueries")) {
    console.error(`${path} still calls invalidateQueries`)
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
