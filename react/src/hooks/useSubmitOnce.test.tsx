import { cleanup, render, screen } from "@testing-library/react"
import { act, useState } from "react"
import { afterEach, describe, expect, it } from "vitest"

import { useSubmitOnce } from "./useSubmitOnce"

function deferred<T>() {
  let resolve: (value: T) => void = () => {}
  let reject: (reason?: unknown) => void = () => {}
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

function Harness({
  onReady,
}: {
  onReady: (api: ReturnType<typeof useSubmitOnce>) => void
}) {
  const submit = useSubmitOnce()
  onReady(submit)
  return <span>{submit.pending ? "pending" : "ready"}</span>
}

function SaveLetter({ send }: { send: () => Promise<string> }) {
  const { pending, run } = useSubmitOnce()
  const [label, setLabel] = useState("idle")
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        void run(send)
          .then((value) => {
            if (value !== undefined) {
              setLabel(value)
            }
          })
          .catch(() => {
            setLabel("error")
          })
      }}
    >
      <button type="submit" disabled={pending}>
        Save
      </button>
      <p>{label}</p>
    </form>
  )
}

afterEach(() => {
  cleanup()
})

describe("useSubmitOnce", () => {
  it("fires once for a same-tick triple call and again after settle", async () => {
    let submit: ReturnType<typeof useSubmitOnce> | undefined
    render(
      <Harness
        onReady={(api) => {
          submit = api
        }}
      />,
    )
    if (!submit) {
      throw new Error("hook did not render")
    }

    const gate = deferred<string>()
    let calls = 0
    const action = () => {
      calls += 1
      return gate.promise
    }

    let first: Promise<string | undefined> = Promise.resolve(undefined)
    act(() => {
      first = submit!.run(action)
      void submit!.run(action)
      void submit!.run(action)
    })

    expect(calls).toBe(1)
    expect(screen.getByText("pending")).toBeTruthy()

    await act(async () => {
      gate.resolve("ok")
      await first
    })

    expect(screen.getByText("ready")).toBeTruthy()
    expect(submit.isLocked()).toBe(false)

    const again = deferred<string>()
    act(() => {
      void submit!.run(() => {
        calls += 1
        return again.promise
      })
    })
    expect(calls).toBe(2)

    await act(async () => {
      again.resolve("ok")
    })
    expect(screen.getByText("ready")).toBeTruthy()
  })

  it("re-enables after the action rejects", async () => {
    let submit: ReturnType<typeof useSubmitOnce> | undefined
    render(
      <Harness
        onReady={(api) => {
          submit = api
        }}
      />,
    )
    if (!submit) {
      throw new Error("hook did not render")
    }

    const gate = deferred<string>()
    let calls = 0
    let first: Promise<string | undefined> = Promise.resolve(undefined)
    act(() => {
      first = submit!.run(() => {
        calls += 1
        return gate.promise
      })
    })
    expect(screen.getByText("pending")).toBeTruthy()

    await act(async () => {
      gate.reject(new Error("nope"))
      await expect(first).rejects.toThrow("nope")
    })

    expect(screen.getByText("ready")).toBeTruthy()
    expect(submit.isLocked()).toBe(false)

    const next = deferred<string>()
    act(() => {
      void submit!.run(() => {
        calls += 1
        return next.promise
      })
    })
    expect(calls).toBe(2)

    await act(async () => {
      next.resolve("ok")
    })
  })

  it("sends one request when Save is triple-clicked", async () => {
    const gate = deferred<string>()
    let calls = 0
    render(
      <SaveLetter
        send={() => {
          calls += 1
          return gate.promise
        }}
      />,
    )
    const button = screen.getByRole("button", { name: "Save" })

    act(() => {
      button.click()
      button.click()
      button.click()
    })

    expect(calls).toBe(1)
    expect((button as HTMLButtonElement).disabled).toBe(true)

    await act(async () => {
      gate.resolve("saved")
    })

    expect((button as HTMLButtonElement).disabled).toBe(false)
    expect(screen.getByText("saved")).toBeTruthy()
  })
})
