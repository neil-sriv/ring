import { getKeyboardShortcutSections } from "../../lib/keyboard"

interface KeyboardShortcutsReferenceProps {
  compact?: boolean
}

export function KeyboardShortcutsReference({
  compact = false,
}: KeyboardShortcutsReferenceProps) {
  const sections = getKeyboardShortcutSections()

  return (
    <div className={compact ? "space-y-3" : "space-y-4 text-sm"}>
      {sections.map((section) => (
        <div key={section.title}>
          <h3
            className={
              compact
                ? "mb-1.5 text-xs font-medium text-muted-foreground"
                : "mb-2 font-medium text-foreground"
            }
          >
            {section.title}
          </h3>
          <dl className={compact ? "space-y-1" : "space-y-2"}>
            {section.shortcuts.map((shortcut) => (
              <div
                key={`${shortcut.keys}-${shortcut.description}`}
                className="flex items-center justify-between gap-4"
              >
                <dt
                  className={
                    compact
                      ? "text-xs text-muted-foreground"
                      : "text-muted-foreground"
                  }
                >
                  {shortcut.description}
                </dt>
                <dd className="shrink-0">
                  <kbd className={compact ? "" : "px-2 text-xs"}>
                    {shortcut.keys}
                  </kbd>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </div>
  )
}
