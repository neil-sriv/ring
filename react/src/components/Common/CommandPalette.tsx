import { useQuery } from "@tanstack/react-query"
import { useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Home, Loader2, LogOut, Search, Settings, Users } from "lucide-react"
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
import { performSearchSearchSearchGetOptions } from "../../client/@tanstack/react-query.gen"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import { modifierKeyLabel } from "../../lib/keyboard"
import { searchResultToCommandItem } from "./searchResultCommand"

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface CommandItem {
  id: string
  label: string
  description?: string
  keywords: string
  icon: React.ComponentType<{ className?: string }>
  action: () => void
  section: "Navigation" | "Groups" | "Actions" | "Search results"
  disabled?: boolean
}

const SEARCH_DEBOUNCE_MS = 300
const SEARCH_MIN_QUERY_LENGTH = 2
const SEARCH_RESULT_LIMIT = 8

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { logout } = useAuth()
  const [query, setQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
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
        action: () => navigate({ to: "/" }),
      },
      {
        id: "nav-groups",
        label: "Groups",
        keywords: "groups",
        icon: Users,
        section: "Navigation",
        action: () => navigate({ to: "/groups" }),
      },
      {
        id: "nav-search",
        label: "Search",
        keywords: "search find",
        icon: Search,
        section: "Navigation",
        action: () => navigate({ to: "/search" }),
      },
      {
        id: "nav-settings",
        label: "Settings",
        keywords: "settings profile preferences",
        icon: Settings,
        section: "Navigation",
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

  const { data: searchData, isFetching: isSearchFetching } = useQuery({
    ...performSearchSearchSearchGetOptions({
      query: {
        query: debouncedQuery,
        limit: SEARCH_RESULT_LIMIT,
      },
    }),
    enabled: open && debouncedQuery.length >= SEARCH_MIN_QUERY_LENGTH,
    staleTime: 0,
    retry: 1,
  })

  const searchItems = useMemo<CommandItem[]>(() => {
    if (!searchData?.results.length) {
      return []
    }

    return searchData.results.map((result) => {
      const searchItem = searchResultToCommandItem(result, navigate)
      return {
        id: searchItem.id,
        label: searchItem.label,
        description: searchItem.description,
        keywords: "",
        icon: searchItem.icon,
        section: "Search results" as const,
        disabled: searchItem.action === null,
        action: searchItem.action ?? (() => {}),
      }
    })
  }, [navigate, searchData])

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

  const displayItems = useMemo(
    () => [...filteredItems, ...searchItems],
    [filteredItems, searchItems],
  )

  const sections = useMemo(() => {
    const orderedSections: CommandItem["section"][] = [
      "Navigation",
      "Groups",
      "Search results",
      "Actions",
    ]
    return orderedSections.filter((section) =>
      displayItems.some((item) => item.section === section),
    )
  }, [displayItems])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(query.trim())
    }, SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(timer)
  }, [query])

  useEffect(() => {
    if (open) {
      setQuery("")
      setDebouncedQuery("")
      setSelectedIndex(0)
      window.requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  useEffect(() => {
    setSelectedIndex(0)
  }, [debouncedQuery])

  useEffect(() => {
    const selectedElement = listRef.current?.querySelector(
      `[data-command-index="${selectedIndex}"]`,
    )
    selectedElement?.scrollIntoView({ block: "nearest" })
  }, [selectedIndex])

  function runItem(item: CommandItem) {
    if (item.disabled) {
      return
    }
    item.action()
    onOpenChange(false)
  }

  function handleInputKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault()
      setSelectedIndex((index) =>
        displayItems.length === 0
          ? 0
          : Math.min(index + 1, displayItems.length - 1),
      )
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      setSelectedIndex((index) => Math.max(index - 1, 0))
      return
    }

    if (event.key === "Enter" && displayItems[selectedIndex]) {
      event.preventDefault()
      runItem(displayItems[selectedIndex])
    }
  }

  const showSearchPending =
    query.trim().length >= SEARCH_MIN_QUERY_LENGTH && isSearchFetching

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-lg">
        <DialogHeader className="sr-only">
          <DialogTitle>Command menu</DialogTitle>
          <DialogDescription>
            Search pages, groups, content, and actions
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
        <div ref={listRef} className="max-h-80 overflow-y-auto p-2">
          {showSearchPending && displayItems.length === 0 ? (
            <div className="flex items-center justify-center gap-2 px-3 py-6 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching…
            </div>
          ) : displayItems.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              No results found.
            </p>
          ) : (
            sections.map((section) => {
              const sectionItems = displayItems.filter(
                (item) => item.section === section,
              )
              if (sectionItems.length === 0) {
                return null
              }

              return (
                <div key={section} className="mb-2 last:mb-0">
                  <div className="flex items-center gap-2 px-2 py-1.5">
                    <p className="text-xs font-medium text-muted-foreground">
                      {section}
                    </p>
                    {section === "Search results" && showSearchPending ? (
                      <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                    ) : null}
                  </div>
                  {sectionItems.map((item) => {
                    const itemIndex = displayItems.indexOf(item)
                    const Icon = item.icon
                    return (
                      <button
                        key={item.id}
                        type="button"
                        data-command-index={itemIndex}
                        onClick={() => runItem(item)}
                        disabled={item.disabled}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm",
                          item.disabled
                            ? "cursor-default opacity-60"
                            : itemIndex === selectedIndex
                              ? "bg-accent text-accent-foreground"
                              : "text-foreground hover:bg-accent/60",
                        )}
                      >
                        <Icon className="h-4 w-4 shrink-0 opacity-70" />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate">{item.label}</span>
                          {item.description ? (
                            <span className="block truncate text-xs text-muted-foreground">
                              {item.description}
                            </span>
                          ) : null}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )
            })
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
