import type { RegisteredRouter } from "@tanstack/react-router"

import { isEditableTarget } from "./keyboard"
import {
  completeGoSequence,
  isGoSequencePending,
  resolveGoSequenceKey,
  startGoSequence,
} from "./keyboardSequence"

const GO_SEQUENCE_TIMEOUT_MS = 1000

interface GlobalShortcutState {
  paletteToggle: (() => void) | null
  helpOpen: (() => void) | null
  modalOpen: () => boolean
}

const state: GlobalShortcutState = {
  paletteToggle: null,
  helpOpen: null,
  modalOpen: () => false,
}

export function registerKeyboardShortcutHandlers(handlers: {
  togglePalette: () => void
  openHelp: () => void
  isModalOpen: () => boolean
}) {
  state.paletteToggle = handlers.togglePalette
  state.helpOpen = handlers.openHelp
  state.modalOpen = handlers.isModalOpen
}

export function initGlobalKeyboardShortcuts(router: RegisteredRouter) {
  function handleKeyDown(event: KeyboardEvent) {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault()
      completeGoSequence()
      state.paletteToggle?.()
      return
    }

    if (state.modalOpen()) {
      return
    }

    if (isEditableTarget(event.target)) {
      if (isGoSequencePending()) {
        completeGoSequence()
      }
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

    if (key === "g") {
      event.preventDefault()
      startGoSequence(() => {}, GO_SEQUENCE_TIMEOUT_MS)
    }
  }

  document.addEventListener("keydown", handleKeyDown, true)
}
