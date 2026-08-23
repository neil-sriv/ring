import { getKeyboardShortcutSections } from "../../lib/keyboard"

export function KeyboardShortcutsReference() {
  const sections = getKeyboardShortcutSections()

  return (
    <div className="space-y-4 text-sm">
      {sections.map((section) => (
        <div key={section.title}>
          <h3 className="mb-2 font-medium text-foreground">{section.title}</h3>
          <dl className="space-y-2">
            {section.shortcuts.map((shortcut) => (
              <div
                key={`${shortcut.keys}-${shortcut.description}`}
                className="flex items-center justify-between gap-4"
              >
                <dt className="text-muted-foreground">
                  {shortcut.description}
                </dt>
                <dd className="shrink-0">
                  <kbd className="px-2 text-xs">{shortcut.keys}</kbd>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </div>
  )
}
