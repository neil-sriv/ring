import { useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Home, LogOut, Search, Settings, Users } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import type { UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import { NAV_ITEM_SHORTCUTS, modifierKeyLabel } from "../../lib/keyboard"
import { KeyboardShortcutsReference } from "./KeyboardShortcutsReference"

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface CommandItem {
  id: string
  label: string
  keywords: string
  icon: React.ComponentType<{ className?: string }>
  action: () => void
  section: "Navigation" | "Groups" | "Actions"
  shortcut?: string
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { logout } = useAuth()
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )

  const groups = currentUser?.groups ?? []

  const items = useMemo<CommandItem[]>(() => {
    const navigationItems: CommandItem[] = [
      {
        id: "nav-home",
        label: "Home",
        keywords: "home dashboard",
        icon: Home,
        section: "Navigation",
        shortcut: NAV_ITEM_SHORTCUTS["/"],
        action: () => navigate({ to: "/" }),
      },
      {
        id: "nav-groups",
        label: "Groups",
        keywords: "groups",
        icon: Users,
        section: "Navigation",
        shortcut: NAV_ITEM_SHORTCUTS["/groups"],
        action: () => navigate({ to: "/groups" }),
      },
      {
        id: "nav-search",
        label: "Search",
        keywords: "search find",
        icon: Search,
        section: "Navigation",
        shortcut: NAV_ITEM_SHORTCUTS["/search"],
        action: () => navigate({ to: "/search" }),
      },
      {
        id: "nav-settings",
        label: "Settings",
        keywords: "settings profile preferences",
        icon: Settings,
        section: "Navigation",
        shortcut: NAV_ITEM_SHORTCUTS["/settings"],
        action: () => navigate({ to: "/settings" }),
      },
    ]

    const groupItems: CommandItem[] = groups.map((group) => ({
      id: `group-${group.api_identifier}`,
      label: group.name,
      keywords: `group ${group.name}`,
      icon: Users,
      section: "Groups",
      action: () =>
        navigate({
          to: "/groups/$groupId/loops",
          params: { groupId: group.api_identifier },
        }),
    }))

    const actionItems: CommandItem[] = [
      {
        id: "action-logout",
        label: "Log out",
        keywords: "logout sign out",
        icon: LogOut,
        section: "Actions",
        action: () => {
          logout()
          queryClient.clear()
        },
      },
    ]

    return [...navigationItems, ...groupItems, ...actionItems]
  }, [groups, logout, navigate, queryClient])

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) {
      return items
    }
    return items.filter(
      (item) =>
        item.label.toLowerCase().includes(normalizedQuery) ||
        item.keywords.toLowerCase().includes(normalizedQuery),
    )
  }, [items, query])

  const showShortcutHelp = query.trim().length === 0

  useEffect(() => {
    if (open) {
      setQuery("")
      setSelectedIndex(0)
      window.requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  useEffect(() => {
    const selectedElement = listRef.current?.querySelector(
      `[data-command-index="${selectedIndex}"]`,
    )
    selectedElement?.scrollIntoView({ block: "nearest" })
  }, [selectedIndex])

  function runItem(item: CommandItem) {
    item.action()
    onOpenChange(false)
  }

  function handleInputKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault()
      setSelectedIndex((index) =>
        filteredItems.length === 0
          ? 0
          : Math.min(index + 1, filteredItems.length - 1),
      )
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      setSelectedIndex((index) => Math.max(index - 1, 0))
      return
    }

    if (event.key === "Enter" && filteredItems[selectedIndex]) {
      event.preventDefault()
      runItem(filteredItems[selectedIndex])
    }
  }

  const sections = ["Navigation", "Groups", "Actions"] as const

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-lg">
        <DialogHeader className="sr-only">
          <DialogTitle>Command menu</DialogTitle>
          <DialogDescription>
            Search pages, groups, and actions
          </DialogDescription>
        </DialogHeader>
        <div className="border-b border-border px-3 py-2">
          <Input
            ref={inputRef}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setSelectedIndex(0)
            }}
            onKeyDown={handleInputKeyDown}
            placeholder={`Search or jump to… (${modifierKeyLabel()}K)`}
            className="h-10 border-0 bg-transparent px-1 shadow-none focus-visible:ring-0"
          />
        </div>
        <div className="flex max-h-[min(32rem,80vh)] flex-col">
          <div ref={listRef} className="flex-1 overflow-y-auto p-2">
            {filteredItems.length === 0 ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                No results found.
              </p>
            ) : (
              sections.map((section) => {
                const sectionItems = filteredItems.filter(
                  (item) => item.section === section,
                )
                if (sectionItems.length === 0) {
                  return null
                }

                return (
                  <div key={section} className="mb-2 last:mb-0">
                    <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                      {section}
                    </p>
                    {sectionItems.map((item) => {
                      const itemIndex = filteredItems.indexOf(item)
                      const Icon = item.icon
                      return (
                        <button
                          key={item.id}
                          type="button"
                          data-command-index={itemIndex}
                          onClick={() => runItem(item)}
                          className={cn(
                            "flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm",
                            itemIndex === selectedIndex
                              ? "bg-accent text-accent-foreground"
                              : "text-foreground hover:bg-accent/60",
                          )}
                        >
                          <Icon className="h-4 w-4 shrink-0 opacity-70" />
                          <span className="flex-1 truncate">{item.label}</span>
                          {item.shortcut && (
                            <kbd className="shrink-0 rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                              {item.shortcut}
                            </kbd>
                          )}
                        </button>
                      )
                    })}
                  </div>
                )
              })
            )}
          </div>
          {showShortcutHelp && (
            <div className="border-t border-border bg-muted/30 px-3 py-3">
              <p className="mb-2 text-xs font-medium text-foreground">
                Keyboard shortcuts
              </p>
              <KeyboardShortcutsReference compact />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
