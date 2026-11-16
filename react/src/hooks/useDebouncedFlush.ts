import { useCallback, useEffect, useRef } from "react"

/**
 * Schedule work after a quiet window, and always flush the latest pending
 * call on unmount / pagehide so tab switches do not drop in-window edits.
 */
export function useDebouncedFlush(flush: () => void, delayMs: number) {
  const flushRef = useRef(flush)
  flushRef.current = flush
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clear = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const flushNow = useCallback(() => {
    clear()
    flushRef.current()
  }, [clear])

  const schedule = useCallback(() => {
    clear()
    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null
      flushRef.current()
    }, delayMs)
  }, [clear, delayMs])

  useEffect(() => {
    const onPageHide = () => {
      flushNow()
    }
    window.addEventListener("pagehide", onPageHide)
    return () => {
      window.removeEventListener("pagehide", onPageHide)
      flushNow()
    }
  }, [flushNow])

  return { schedule, flushNow, clear }
}
