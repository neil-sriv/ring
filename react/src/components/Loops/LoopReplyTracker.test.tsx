import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import type { PublicLetter, PublicQuestion, UserUnlinked } from "../../client"
import { LoopReplyTracker } from "./LoopReplyTracker"

function person(name: string, id: string): UserUnlinked {
  return {
    email: `${id}@example.com`,
    name,
    api_identifier: id,
    admin: false,
  }
}

const ada = person("Ada", "usr_ada")
const bo = person("Bo", "usr_bo")
const cy = person("Cy", "usr_cy")
const dee = person("Dee", "usr_dee")

function question(
  id: string,
  text: string,
  position: number,
  respondents: UserUnlinked[],
  addedLate = false,
): PublicQuestion {
  return {
    question_text: text,
    api_identifier: id,
    created_at: "2026-11-01T00:00:00.000Z",
    position,
    added_late: addedLate,
    author: ada,
    responses: respondents.map((respondent, index) => ({
      response_text: "Answered.",
      api_identifier: `${id}_${index}`,
      created_at: "2026-11-02T00:00:00.000Z",
      participant: respondent,
      images: [],
    })),
  }
}

function letter(questions: PublicQuestion[]): PublicLetter {
  return {
    api_identifier: "lttr_test",
    status: "IN_PROGRESS",
    send_at: "2026-12-01T00:00:00.000Z",
    created_at: "2026-11-01T00:00:00.000Z",
    title: "Weekly",
    letter_type: "CYCLIC",
    group: {
      api_identifier: "grp_test",
      name: "Test Group",
      created_at: "2026-11-01T00:00:00.000Z",
      cycle_length: 7,
    },
    questions,
    responders: [ada, bo, cy],
    participants: [ada, bo, cy, dee],
  }
}

function chip(name: string): HTMLElement {
  const item = screen.getByText(name).closest("li")
  if (!item) {
    throw new Error(`missing chip for ${name}`)
  }
  return item
}

afterEach(() => {
  cleanup()
})

describe("LoopReplyTracker", () => {
  it("shows 3/4 on a quieter chip and a header after a late question", () => {
    render(
      <LoopReplyTracker
        loop={letter([
          question("q1", "One?", 1, [ada, bo, cy]),
          question("q2", "Two?", 2, [ada, bo, cy]),
          question("q3", "Three?", 3, [ada, cy]),
          question("q4", "What did you forget?", 0, [cy], true),
        ])}
      />,
    )

    expect(screen.getByText("2 have unanswered questions")).toBeTruthy()
    expect(screen.getByText(/3 of 4 participants replied/)).toBeTruthy()
    expect(screen.getByText("Replied (3)")).toBeTruthy()
    expect(screen.getByText(/Waiting on \(1\)/)).toBeTruthy()

    const adaChip = chip("Ada")
    expect(adaChip.textContent).toContain("3/4")
    expect(adaChip.getAttribute("data-completion")).toBe("partial")
    expect(adaChip.className).toContain("text-muted-foreground")
    expect(adaChip.className).not.toContain("bg-success/10")
    expect(adaChip.className).not.toContain("text-success")

    const boChip = chip("Bo")
    expect(boChip.textContent).toContain("2/4")
    expect(boChip.getAttribute("data-completion")).toBe("partial")

    const cyChip = chip("Cy")
    expect(cyChip.textContent).toContain("4/4")
    expect(cyChip.getAttribute("data-completion")).toBe("full")
    expect(cyChip.className).toContain("bg-success/10")
    expect(cyChip.className).toContain("text-success")

    const deeChip = chip("Dee")
    expect(deeChip.getAttribute("data-completion")).toBe("none")
    expect(deeChip.className).toContain("bg-muted")
  })

  it("leaves the header off when everyone who replied answered every question", () => {
    render(
      <LoopReplyTracker
        loop={letter([
          question("q1", "One?", 0, [ada, bo, cy]),
          question("q2", "Two?", 1, [ada, bo, cy], true),
        ])}
      />,
    )

    expect(screen.queryByText(/unanswered questions/)).toBeNull()
    expect(chip("Ada").getAttribute("data-completion")).toBe("full")
    expect(chip("Ada").textContent).toContain("2/2")
    expect(screen.getByText(/3 of 4 participants replied/)).toBeTruthy()
  })
})
