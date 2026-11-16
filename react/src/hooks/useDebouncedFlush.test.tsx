import { cleanup, render } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { useDebouncedFlush } from "./useDebouncedFlush"

function Harness({
  flush,
  delayMs,
  onReady,
}: {
  flush: () => void
  delayMs: number
  onReady: (api: ReturnType<typeof useDebouncedFlush>) => void
}) {
  const api = useDebouncedFlush(flush, delayMs)
  onReady(api)
  return null
}

describe("useDebouncedFlush", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
  })

  it("coalesces rapid schedule calls into one flush after the delay", () => {
    const flush = vi.fn()
    let api: ReturnType<typeof useDebouncedFlush> | undefined
    render(
      <Harness
        flush={flush}
        delayMs={1000}
        onReady={(value) => {
          api = value
        }}
      />,
    )

    api!.schedule()
    api!.schedule()
    api!.schedule()
    expect(flush).not.toHaveBeenCalled()

    vi.advanceTimersByTime(999)
    expect(flush).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(flush).toHaveBeenCalledTimes(1)
  })

  it("flushes immediately on flushNow and cancels the pending timer", () => {
    const flush = vi.fn()
    let api: ReturnType<typeof useDebouncedFlush> | undefined
    render(
      <Harness
        flush={flush}
        delayMs={1000}
        onReady={(value) => {
          api = value
        }}
      />,
    )

    api!.schedule()
    api!.flushNow()
    expect(flush).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    expect(flush).toHaveBeenCalledTimes(1)
  })

  it("flushes a pending schedule on unmount", () => {
    const flush = vi.fn()
    let api: ReturnType<typeof useDebouncedFlush> | undefined
    const view = render(
      <Harness
        flush={flush}
        delayMs={1000}
        onReady={(value) => {
          api = value
        }}
      />,
    )

    api!.schedule()
    expect(flush).not.toHaveBeenCalled()

    view.unmount()
    expect(flush).toHaveBeenCalledTimes(1)
  })

  it("flushes a pending schedule on pagehide", () => {
    const flush = vi.fn()
    let api: ReturnType<typeof useDebouncedFlush> | undefined
    render(
      <Harness
        flush={flush}
        delayMs={1000}
        onReady={(value) => {
          api = value
        }}
      />,
    )

    api!.schedule()
    expect(flush).not.toHaveBeenCalled()

    window.dispatchEvent(new Event("pagehide"))
    expect(flush).toHaveBeenCalledTimes(1)
  })
})
