import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import type { PublicQuestion, UserUnlinked } from "../../client"
import PublishedQuestion from "./PublishedQuestion"

function person(name: string, id: string): UserUnlinked {
  return {
    email: `${id}@example.com`,
    name,
    api_identifier: id,
    admin: false,
  }
}

function question(addedLate: boolean): PublicQuestion {
  return {
    question_text: "What did you forget?",
    api_identifier: "q_late",
    created_at: "2026-11-10T00:00:00.000Z",
    position: 0,
    added_late: addedLate,
    author: person("Ada", "usr_ada"),
    responses: [
      {
        response_text: "This, after send.",
        api_identifier: "resp_1",
        created_at: "2026-11-12T00:00:00.000Z",
        participant: person("Bo", "usr_bo"),
        images: [],
      },
    ],
  }
}

function renderQuestion(addedLate: boolean) {
  return render(
    <PublishedQuestion
      question={question(addedLate)}
      letterSendAt="2026-11-01T00:00:00.000Z"
    />,
  )
}

afterEach(() => {
  cleanup()
})

describe("PublishedQuestion late badge", () => {
  it("shows a Late badge that does not look like Late Answer", () => {
    renderQuestion(true)

    const lateQuestion = screen.getByText("Late")
    const lateAnswer = screen.getByText("Late Answer")
    expect(lateQuestion.className).toContain("text-warning")
    expect(lateQuestion.className).toContain("bg-warning/10")
    expect(lateQuestion.className).not.toContain("text-info")
    expect(lateQuestion.className).not.toContain("bg-info/10")
    expect(lateAnswer.className).toContain("text-info")
    expect(lateAnswer.className).toContain("bg-info/10")
    expect(lateAnswer.className).not.toContain("text-warning")
    expect(lateAnswer.className).not.toContain("bg-warning/10")
  })

  it("hides the Late badge when the question was not added late", () => {
    renderQuestion(false)

    expect(screen.queryByText("Late")).toBeNull()
    expect(screen.getByText("Late Answer")).toBeTruthy()
  })
})
