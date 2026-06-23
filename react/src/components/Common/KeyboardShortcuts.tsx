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
import { GO_TO_SHORTCUTS, modifierKeyLabel } from "../../lib/keyboard"
import { subscribeGoSequencePending } from "../../lib/keyboardSequence"
import { CommandPalette } from "./CommandPalette"

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
            "rounded-md border border-border bg-background/95 px-3 py-2 text-sm shadow-md",
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
        <div className="space-y-4 text-sm">
          <ShortcutSection
            title="General"
            shortcuts={[
              {
                keys: `${modifierKeyLabel()} K`,
                description: "Open command menu",
              },
              { keys: "?", description: "Show keyboard shortcuts" },
            ]}
          />
          <ShortcutSection
            title="Go to"
            shortcuts={GO_TO_SHORTCUTS.map((shortcut) => ({
              keys: shortcut.keys,
              description: shortcut.label,
            }))}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}

interface ShortcutSectionProps {
  title: string
  shortcuts: Array<{ keys: string; description: string }>
}

function ShortcutSection({ title, shortcuts }: ShortcutSectionProps) {
  return (
    <div>
      <h3 className="mb-2 font-medium text-foreground">{title}</h3>
      <dl className="space-y-2">
        {shortcuts.map((shortcut) => (
          <div
            key={`${shortcut.keys}-${shortcut.description}`}
            className="flex items-center justify-between gap-4"
          >
            <dt className="text-muted-foreground">{shortcut.description}</dt>
            <dd>
              <kbd className="rounded border border-border bg-muted px-2 py-0.5 font-mono text-xs text-foreground">
                {shortcut.keys}
              </kbd>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
