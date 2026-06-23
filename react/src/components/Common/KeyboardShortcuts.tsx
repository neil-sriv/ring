import { useNavigate } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import {
  GO_TO_ROUTE_KEYS,
  GO_TO_SHORTCUTS,
  isEditableTarget,
  modifierKeyLabel,
} from "../../lib/keyboard"
import { CommandPalette } from "./CommandPalette"

const GO_SEQUENCE_TIMEOUT_MS = 1000

export function KeyboardShortcuts() {
  const navigate = useNavigate()
  const navigateRef = useRef(navigate)
  const pendingGoKeyRef = useRef(false)
  const goTimeoutRef = useRef<number | null>(null)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const [goPending, setGoPending] = useState(false)
  const shortcutsEnabled = !paletteOpen && !helpOpen

  navigateRef.current = navigate

  useEffect(() => {
    function clearGoSequence() {
      pendingGoKeyRef.current = false
      setGoPending(false)
      if (goTimeoutRef.current !== null) {
        window.clearTimeout(goTimeoutRef.current)
        goTimeoutRef.current = null
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        clearGoSequence()
        setPaletteOpen((open) => !open)
        return
      }

      if (!shortcutsEnabled || isEditableTarget(event.target)) {
        clearGoSequence()
        return
      }

      if (
        event.key === "?" &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.altKey
      ) {
        event.preventDefault()
        clearGoSequence()
        setHelpOpen(true)
        return
      }

      const key = event.key.toLowerCase()

      if (pendingGoKeyRef.current) {
        const destination = GO_TO_ROUTE_KEYS[key]
        clearGoSequence()
        if (destination) {
          event.preventDefault()
          navigateRef.current({ to: destination })
        }
        return
      }

      if (key === "g") {
        event.preventDefault()
        pendingGoKeyRef.current = true
        setGoPending(true)
        goTimeoutRef.current = window.setTimeout(
          clearGoSequence,
          GO_SEQUENCE_TIMEOUT_MS,
        )
      }
    }

    window.addEventListener("keydown", handleKeyDown, true)
    return () => {
      window.removeEventListener("keydown", handleKeyDown, true)
    }
  }, [shortcutsEnabled])

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
