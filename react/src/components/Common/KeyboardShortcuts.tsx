import { useEffect, useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useGoToShortcuts } from "../../hooks/useGoToShortcuts"
import {
  GO_TO_SHORTCUTS,
  isEditableTarget,
  modifierKeyLabel,
} from "../../lib/keyboard"
import { CommandPalette } from "./CommandPalette"

export function KeyboardShortcuts() {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const shortcutsEnabled = !paletteOpen && !helpOpen

  useGoToShortcuts({ enabled: shortcutsEnabled })

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setPaletteOpen((open) => !open)
        return
      }

      if (!shortcutsEnabled || isEditableTarget(event.target)) {
        return
      }

      if (
        event.key === "?" &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.altKey
      ) {
        event.preventDefault()
        setHelpOpen(true)
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [shortcutsEnabled])

  return (
    <>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
      <KeyboardShortcutsHelp open={helpOpen} onOpenChange={setHelpOpen} />
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
