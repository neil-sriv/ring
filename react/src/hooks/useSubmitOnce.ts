import { useCallback, useRef, useState } from "react"

/**
 * One in-flight submit.
 *
 * `isPending` / `isSubmitting` flip on the next render, so a second call in
 * the same turn still enters the handler. `run` takes a ref synchronously
 * and ignores re-entry until the action settles, including when it throws.
 * `pending` stays true for that whole window so the control can be disabled.
 * `isLocked` reads the ref for checks that must run before the re-render.
 */
export function useSubmitOnce() {
  const inFlightRef = useRef(false)
  const [pending, setPending] = useState(false)

  const isLocked = useCallback(() => inFlightRef.current, [])

  const run = useCallback(
    async <T>(action: () => Promise<T>): Promise<T | undefined> => {
      if (inFlightRef.current) {
        return undefined
      }
      inFlightRef.current = true
      setPending(true)
      try {
        return await action()
      } finally {
        inFlightRef.current = false
        setPending(false)
      }
    },
    [],
  )

  return { pending, isLocked, run }
}
