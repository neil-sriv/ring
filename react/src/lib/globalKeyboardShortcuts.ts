import type { RegisteredRouter } from "@tanstack/react-router"

import { isEditableTarget } from "./keyboard"
import {
  completeGoSequence,
  isGoSequencePending,
  resolveGoSequenceKey,
  startGoSequence,
} from "./keyboardSequence"

const GO_SEQUENCE_TIMEOUT_MS = 1000
let initialized = false

interface GlobalShortcutState {
  paletteToggle: (() => void) | null
  helpOpen: (() => void) | null
  isHelpOpen: () => boolean
  searchFocus: (() => void) | null
}

const state: GlobalShortcutState = {
  paletteToggle: null,
  helpOpen: null,
  isHelpOpen: () => false,
  searchFocus: null,
}

export function registerKeyboardShortcutHandlers(handlers: {
  togglePalette: () => void
  openHelp: () => void
  isHelpOpen: () => boolean
}) {
  state.paletteToggle = handlers.togglePalette
  state.helpOpen = handlers.openHelp
  state.isHelpOpen = handlers.isHelpOpen
}

export function registerSearchFocusHandler(handler: (() => void) | null) {
  state.searchFocus = handler
}

function shouldIgnoreShortcuts(event: KeyboardEvent) {
  return (
    isEditableTarget(event.target) || isEditableTarget(document.activeElement)
  )
}

export function initGlobalKeyboardShortcuts(router: RegisteredRouter) {
  if (initialized) {
    return
  }
  initialized = true

  function handleKeyDown(event: KeyboardEvent) {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault()
      completeGoSequence()
      state.paletteToggle?.()
      return
    }

    if (state.isHelpOpen()) {
      return
    }

    const key = event.key.toLowerCase()

    if (isGoSequencePending()) {
      const destination = resolveGoSequenceKey(key)
      completeGoSequence()
      if (destination) {
        event.preventDefault()
        router.navigate({ to: destination })
        if (destination === "/search") {
          // Already on /search: the route doesn't remount, so its mount-time
          // focus won't run again. Refocus the registered search input.
          state.searchFocus?.()
        }
      }
      return
    }

    if (shouldIgnoreShortcuts(event)) {
      return
    }

    if (
      event.key === "?" &&
      !event.metaKey &&
      !event.ctrlKey &&
      !event.altKey
    ) {
      event.preventDefault()
      completeGoSequence()
      state.helpOpen?.()
      return
    }

    if (key === "g" || event.code === "KeyG") {
      event.preventDefault()
      startGoSequence(() => {}, GO_SEQUENCE_TIMEOUT_MS)
    }
  }

  document.addEventListener("keydown", handleKeyDown, true)
}
