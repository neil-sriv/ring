import assert from "node:assert/strict"
import test from "node:test"

import {
  movedQuestionIds,
  questionsInDisplayOrder,
  withQuestionPositions,
} from "./questionOrder.ts"

const questions = [
  {
    api_identifier: "q_a",
    position: 0,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    api_identifier: "q_b",
    position: 1,
    created_at: "2026-01-02T00:00:00Z",
  },
  {
    api_identifier: "q_c",
    position: 2,
    created_at: "2026-01-03T00:00:00Z",
  },
]

test("display order follows position, not creation time", () => {
  const shuffled = [questions[2], questions[0], questions[1]]
  assert.deepEqual(
    questionsInDisplayOrder(shuffled).map(
      (question) => question.api_identifier,
    ),
    ["q_a", "q_b", "q_c"],
  )
})

test("moving a question returns the full permutation", () => {
  assert.deepEqual(movedQuestionIds(["q_a", "q_b", "q_c"], 2, -1), [
    "q_a",
    "q_c",
    "q_b",
  ])
  assert.equal(movedQuestionIds(["q_a", "q_b"], 0, -1), undefined)
})

test("positions are rewritten to match the submitted order", () => {
  const next = withQuestionPositions(questions, ["q_c", "q_a", "q_b"])
  assert.deepEqual(
    next.map((question) => [question.api_identifier, question.position]),
    [
      ["q_c", 0],
      ["q_a", 1],
      ["q_b", 2],
    ],
  )
  assert.equal(questions[0].position, 0)
})
