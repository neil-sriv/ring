export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  const tagName = target.tagName
  if (tagName === "INPUT" || tagName === "TEXTAREA" || tagName === "SELECT") {
    return true
  }

  if (target.isContentEditable) {
    return true
  }

  return Boolean(target.closest("[contenteditable='true']"))
}

export function isMacPlatform(): boolean {
  if (typeof navigator === "undefined") {
    return false
  }
  return /Mac|iPhone|iPad|iPod/.test(navigator.platform)
}

export function modifierKeyLabel(): string {
  return isMacPlatform() ? "⌘" : "Ctrl"
}

export interface GoToShortcut {
  keys: string
  label: string
  path: "/" | "/groups" | "/search" | "/settings"
}

export const GO_TO_SHORTCUTS: GoToShortcut[] = [
  { keys: "g h", label: "Home", path: "/" },
  { keys: "g g", label: "Groups", path: "/groups" },
  { keys: "g s", label: "Search", path: "/search" },
  { keys: "g p", label: "Settings", path: "/settings" },
]

export const GO_TO_ROUTE_KEYS: Record<string, GoToShortcut["path"]> = {
  h: "/",
  g: "/groups",
  s: "/search",
  p: "/settings",
}
