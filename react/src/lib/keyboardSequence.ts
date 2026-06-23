import type { GoToShortcut } from "./keyboard"

let goSequencePending = false
let goSequenceTimeout: number | null = null
const goSequenceListeners = new Set<(pending: boolean) => void>()

export function setGoSequencePending(pending: boolean) {
  goSequencePending = pending
  for (const listener of goSequenceListeners) {
    listener(pending)
  }
}

export function isGoSequencePending() {
  return goSequencePending
}

export function clearGoSequenceTimeout() {
  if (goSequenceTimeout !== null) {
    window.clearTimeout(goSequenceTimeout)
    goSequenceTimeout = null
  }
}

export function startGoSequence(onExpire: () => void, timeoutMs: number) {
  clearGoSequenceTimeout()
  goSequencePending = true
  setGoSequencePending(true)
  goSequenceTimeout = window.setTimeout(() => {
    goSequencePending = false
    setGoSequencePending(false)
    onExpire()
  }, timeoutMs)
}

export function completeGoSequence() {
  clearGoSequenceTimeout()
  goSequencePending = false
  setGoSequencePending(false)
}

export function subscribeGoSequencePending(
  listener: (pending: boolean) => void,
) {
  goSequenceListeners.add(listener)
  listener(goSequencePending)
  return () => {
    goSequenceListeners.delete(listener)
  }
}

export function resolveGoSequenceKey(
  key: string,
): GoToShortcut["path"] | undefined {
  const destinations: Record<string, GoToShortcut["path"]> = {
    h: "/",
    g: "/groups",
    s: "/search",
    p: "/settings",
  }
  return destinations[key]
}
