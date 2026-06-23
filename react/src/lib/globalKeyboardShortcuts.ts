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
}

const state: GlobalShortcutState = {
  paletteToggle: null,
  helpOpen: null,
  isHelpOpen: () => false,
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
