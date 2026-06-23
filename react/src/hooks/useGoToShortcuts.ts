import { useNavigate } from "@tanstack/react-router"
import { useEffect, useRef } from "react"

import { GO_TO_ROUTE_KEYS, isEditableTarget } from "../lib/keyboard"

interface UseGoToShortcutsOptions {
  enabled?: boolean
}

const SEQUENCE_TIMEOUT_MS = 1000

export function useGoToShortcuts({
  enabled = true,
}: UseGoToShortcutsOptions = {}) {
  const navigate = useNavigate()
  const navigateRef = useRef(navigate)
  const pendingKeyRef = useRef<string | null>(null)
  const timeoutRef = useRef<number | null>(null)

  navigateRef.current = navigate

  useEffect(() => {
    if (!enabled) {
      pendingKeyRef.current = null
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      return
    }

    function clearPending() {
      pendingKeyRef.current = null
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) {
        clearPending()
        return
      }

      if (event.metaKey || event.ctrlKey || event.altKey) {
        clearPending()
        return
      }

      if (event.key === "Escape") {
        clearPending()
        return
      }

      const key = event.key.toLowerCase()

      if (pendingKeyRef.current === "g") {
        const destination = GO_TO_ROUTE_KEYS[key]
        clearPending()
        if (destination) {
          event.preventDefault()
          navigateRef.current({ to: destination })
        }
        return
      }

      if (key === "g") {
        event.preventDefault()
        pendingKeyRef.current = "g"
        timeoutRef.current = window.setTimeout(
          clearPending,
          SEQUENCE_TIMEOUT_MS,
        )
      }
    }

    window.addEventListener("keydown", handleKeyDown, true)
    return () => {
      window.removeEventListener("keydown", handleKeyDown, true)
    }
  }, [enabled])
}
