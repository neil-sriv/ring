import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"

import { EDIT_LOOP_PRE_421_SOURCE } from "./fixtures/edit-loop-pre-421.ts"
import type { MutationCacheId } from "./queryCachePolicy.ts"
import {
  invalidatedQueryIds,
  missingPolicyQueryIds,
  policyQueryIds,
} from "./queryCachePolicy.ts"
import type { useAppMutation } from "./useAppMutation.ts"

type AppMutationOptions = Parameters<typeof useAppMutation>[0]
type CacheRequired = AppMutationOptions extends { cache: MutationCacheId }
  ? true
  : false
const cacheIsRequired: CacheRequired = true

type PastMistakeId = "editLetterDetailOnly"
type PastIdRejected = PastMistakeId extends MutationCacheId ? true : false
const pastIdRejected: PastIdRejected = false

test("useAppMutation requires a table cache id", () => {
  assert.equal(cacheIsRequired, true)
  assert.equal(pastIdRejected, false)
})

test("editLetter policy owns letter, list, and dashboard", () => {
  assert.deepEqual(policyQueryIds("editLetter"), [
    "readLetterLettersLetterLetterApiIdGet",
    "listLettersLettersLettersGet",
    "listDashboardLettersLettersLettersDashboardGet",
  ])
})

test("reconstructed f0d0533^ EditLoop misses list and dashboard", () => {
  const invalidated = invalidatedQueryIds(EDIT_LOOP_PRE_421_SOURCE)
  assert.deepEqual(invalidated, ["readLetterLettersLetterLetterApiIdGet"])
  assert.deepEqual(missingPolicyQueryIds("editLetter", invalidated), [
    "listLettersLettersLettersGet",
    "listDashboardLettersLettersLettersDashboardGet",
  ])
})

test("EditLoop no longer invalidates from the component", () => {
  const source = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "../components/Loops/EditLoop.tsx",
    ),
    "utf8",
  )
  assert.match(source, /cache:\s*"editLetter"/)
  assert.doesNotMatch(source, /invalidateQueries/)
})
