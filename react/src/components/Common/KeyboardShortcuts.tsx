import { useEffect, useRef, useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { registerKeyboardShortcutHandlers } from "../../lib/globalKeyboardShortcuts"
import { subscribeGoSequencePending } from "../../lib/keyboardSequence"
import { CommandPalette } from "./CommandPalette"
import { KeyboardShortcutsReference } from "./KeyboardShortcutsReference"

export function KeyboardShortcuts() {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const [goPending, setGoPending] = useState(false)
  const helpOpenRef = useRef(helpOpen)

  helpOpenRef.current = helpOpen

  useEffect(() => subscribeGoSequencePending(setGoPending), [])

  useEffect(() => {
    registerKeyboardShortcutHandlers({
      togglePalette: () => setPaletteOpen((open) => !open),
      openHelp: () => setHelpOpen(true),
      isHelpOpen: () => helpOpenRef.current,
    })
  }, [])

  return (
    <>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
      <KeyboardShortcutsHelp open={helpOpen} onOpenChange={setHelpOpen} />
      {goPending && (
        <div
          className={cn(
            "pointer-events-none fixed bottom-4 left-1/2 z-50 -translate-x-1/2",
            "rounded-lg border border-border bg-popover px-3 py-2 text-sm text-popover-foreground shadow-md",
          )}
        >
          Go to… h home, g groups, s search, p settings
        </div>
      )}
    </>
  )
}

interface KeyboardShortcutsHelpProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function KeyboardShortcutsHelp({
  open,
  onOpenChange,
}: KeyboardShortcutsHelpProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
          <DialogDescription>
            Navigate quickly without leaving the keyboard.
          </DialogDescription>
        </DialogHeader>
        <KeyboardShortcutsReference />
      </DialogContent>
    </Dialog>
  )
}
