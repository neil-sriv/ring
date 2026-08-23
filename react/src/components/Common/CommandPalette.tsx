import {
  keepPreviousData,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import {
  Home,
  Loader2,
  LogOut,
  Mail,
  MessageCircleQuestion,
  MessageSquare,
  Search,
  Settings,
  Users,
} from "lucide-react"
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
import type { SearchHit, SearchableType, UserLinked } from "../../client"
import {
  performSearchSearchSearchGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import { useDebouncedValue } from "../../hooks/useDebouncedValue"
import { NAV_ITEM_SHORTCUTS, modifierKeyLabel } from "../../lib/keyboard"

const MIN_SEARCH_QUERY_LENGTH = 2
const SEARCH_RESULT_LIMIT = 20
const SEARCH_DEBOUNCE_MS = 250

// Sorted alphabetically so the query key is stable. `user` hits are excluded:
// they have no destination to navigate to, which makes them dead rows in a
// palette where every entry is expected to run something.
const PALETTE_SEARCH_TYPES: SearchableType[] = [
  "group",
  "letter",
  "question",
  "response",
]

type PaletteSection = "Pages" | "Groups" | "Letters" | "Actions"

const PALETTE_TABS = [
  { id: "all", label: "All" },
  { id: "pages", label: "Pages" },
  { id: "groups", label: "Groups" },
  { id: "letters", label: "Letters" },
  { id: "actions", label: "Actions" },
] as const

type PaletteTabId = (typeof PALETTE_TABS)[number]["id"]

const SECTIONS_BY_TAB: Record<PaletteTabId, PaletteSection[]> = {
  all: ["Pages", "Groups", "Letters", "Actions"],
  pages: ["Pages"],
  groups: ["Groups"],
  letters: ["Letters"],
  actions: ["Actions"],
}

type LetterHitType = "letter" | "question" | "response"

const LETTER_HIT_ICONS: Record<
  LetterHitType,
  React.ComponentType<{ className?: string }>
> = {
  letter: Mail,
  question: MessageCircleQuestion,
  response: MessageSquare,
}

const LETTER_HIT_LABELS: Record<LetterHitType, string> = {
  letter: "Letter",
  question: "Question",
  response: "Response",
}

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onOpenShortcutHelp: () => void
}

interface PaletteEntry {
  id: string
  title: string
  subtitle?: string
  keywords?: string
  icon: React.ComponentType<{ className?: string }>
  // Pinned entries (e.g. "Search everywhere") have no section: they are
  // rendered outside the sectioned list and shown on every tab.
  section?: PaletteSection
  shortcut?: string
  typeLabel?: string
  run: () => void
}

function matchesQuery(entry: PaletteEntry, normalizedQuery: string): boolean {
  return (
    entry.title.toLowerCase().includes(normalizedQuery) ||
    (entry.keywords?.toLowerCase().includes(normalizedQuery) ?? false)
  )
}

export function CommandPalette({
  open,
  onOpenChange,
  onOpenShortcutHelp,
}: CommandPaletteProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { logout } = useAuth()
  const [query, setQuery] = useState("")
  const [activeTab, setActiveTab] = useState<PaletteTabId>("all")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )

  const groups = currentUser?.groups ?? []

  const trimmedQuery = query.trim()
  const normalizedQuery = trimmedQuery.toLowerCase()
  const debouncedQuery = useDebouncedValue(trimmedQuery, SEARCH_DEBOUNCE_MS)
  const searchActive = trimmedQuery.length >= MIN_SEARCH_QUERY_LENGTH

  const {
    data: searchData,
    isFetching: searchFetching,
    isError: searchFailed,
  } = useQuery({
    ...performSearchSearchSearchGetOptions({
      query: {
        query: debouncedQuery,
        limit: SEARCH_RESULT_LIMIT,
        types: PALETTE_SEARCH_TYPES,
      },
    }),
    enabled: open && debouncedQuery.length >= MIN_SEARCH_QUERY_LENGTH,
    placeholderData: keepPreviousData,
  })

  const searchLoading =
    searchActive && (debouncedQuery !== trimmedQuery || searchFetching)

  const staticEntries = useMemo<PaletteEntry[]>(() => {
    const pageEntries: PaletteEntry[] = [
      {
        id: "nav-home",
        title: "Home",
        keywords: "home dashboard",
        icon: Home,
        section: "Pages",
        shortcut: NAV_ITEM_SHORTCUTS["/"],
        run: () => navigate({ to: "/" }),
      },
      {
        id: "nav-groups",
        title: "Groups",
        keywords: "groups",
        icon: Users,
        section: "Pages",
        shortcut: NAV_ITEM_SHORTCUTS["/groups"],
        run: () => navigate({ to: "/groups" }),
      },
      {
        id: "nav-search",
        title: "Search",
        keywords: "search find",
        icon: Search,
        section: "Pages",
        shortcut: NAV_ITEM_SHORTCUTS["/search"],
        run: () => navigate({ to: "/search" }),
      },
      {
        id: "nav-settings",
        title: "Settings",
        keywords: "settings profile preferences",
        icon: Settings,
        section: "Pages",
        shortcut: NAV_ITEM_SHORTCUTS["/settings"],
        run: () => navigate({ to: "/settings" }),
      },
    ]

    const groupEntries: PaletteEntry[] = groups.map((group) => ({
      id: `group-${group.api_identifier}`,
      title: group.name,
      keywords: `group ${group.name}`,
      icon: Users,
      section: "Groups",
      run: () =>
        navigate({
          to: "/groups/$groupId/loops",
          params: { groupId: group.api_identifier },
        }),
    }))

    const actionEntries: PaletteEntry[] = [
      {
        id: "action-logout",
        title: "Log out",
        keywords: "logout sign out",
        icon: LogOut,
        section: "Actions",
        run: () => {
          logout()
          queryClient.clear()
        },
      },
    ]

    return [...pageEntries, ...groupEntries, ...actionEntries]
  }, [groups, logout, navigate, queryClient])

  const filteredStaticEntries = useMemo(() => {
    if (!normalizedQuery) {
      return staticEntries
    }
    return staticEntries.filter((entry) => matchesQuery(entry, normalizedQuery))
  }, [staticEntries, normalizedQuery])

  const searchEntries = useMemo<PaletteEntry[]>(() => {
    if (!searchActive) {
      return []
    }
    const staticIds = new Set(filteredStaticEntries.map((entry) => entry.id))
    const hits = searchData?.results ?? []

    return hits.flatMap<PaletteEntry>((hit: SearchHit) => {
      if (hit.type === "group" && hit.href_group_id) {
        const groupId = hit.href_group_id
        const id = `group-${hit.api_identifier}`
        // Skip hits already shown as one of the user's own groups.
        if (staticIds.has(id)) {
          return []
        }
        return [
          {
            id,
            title: hit.title,
            subtitle: hit.subtitle ?? undefined,
            icon: Users,
            section: "Groups",
            run: () =>
              navigate({
                to: "/groups/$groupId/loops",
                params: { groupId },
              }),
          },
        ]
      }

      if (
        (hit.type === "letter" ||
          hit.type === "question" ||
          hit.type === "response") &&
        hit.href_loop_id
      ) {
        const loopId = hit.href_loop_id
        return [
          {
            id: `hit-${hit.type}-${hit.api_identifier}`,
            title: hit.title,
            subtitle: hit.subtitle ?? undefined,
            icon: LETTER_HIT_ICONS[hit.type],
            section: "Letters",
            typeLabel: LETTER_HIT_LABELS[hit.type],
            run: () => navigate({ to: "/loops/$loopId", params: { loopId } }),
          },
        ]
      }

      return []
    })
  }, [filteredStaticEntries, navigate, searchActive, searchData])

  const sectionedEntries = useMemo(() => {
    const allEntries = [...filteredStaticEntries, ...searchEntries]
    return SECTIONS_BY_TAB[activeTab]
      .map((section) => ({
        section,
        entries: allEntries.filter((entry) => entry.section === section),
      }))
      .filter(({ entries }) => entries.length > 0)
  }, [activeTab, filteredStaticEntries, searchEntries])

  const handoffEntry = useMemo<PaletteEntry | null>(() => {
    if (!trimmedQuery) {
      return null
    }
    return {
      id: "search-everywhere",
      title: `Search everywhere for "${trimmedQuery}"`,
      icon: Search,
      run: () => navigate({ to: "/search", search: { q: trimmedQuery } }),
    }
  }, [navigate, trimmedQuery])

  const visibleEntries = useMemo(() => {
    const entries = sectionedEntries.flatMap(({ entries }) => entries)
    return handoffEntry ? [...entries, handoffEntry] : entries
  }, [handoffEntry, sectionedEntries])

  useEffect(() => {
    if (open) {
      setQuery("")
      setActiveTab("all")
      setSelectedIndex(0)
      window.requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  useEffect(() => {
    setSelectedIndex((index) =>
      visibleEntries.length === 0
        ? 0
        : Math.min(index, visibleEntries.length - 1),
    )
  }, [visibleEntries.length])

  useEffect(() => {
    const selectedElement = listRef.current?.querySelector(
      `[data-command-index="${selectedIndex}"]`,
    )
    selectedElement?.scrollIntoView({ block: "nearest" })
  }, [selectedIndex])

  function runEntry(entry: PaletteEntry) {
    entry.run()
    onOpenChange(false)
  }

  function selectTab(tabId: PaletteTabId) {
    setActiveTab(tabId)
    setSelectedIndex(0)
    listRef.current?.scrollTo({ top: 0 })
  }

  function cycleTab(direction: 1 | -1) {
    const currentIndex = PALETTE_TABS.findIndex((tab) => tab.id === activeTab)
    const nextIndex =
      (currentIndex + direction + PALETTE_TABS.length) % PALETTE_TABS.length
    selectTab(PALETTE_TABS[nextIndex].id)
  }

  function handleInputKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Tab") {
      event.preventDefault()
      cycleTab(event.shiftKey ? -1 : 1)
      return
    }

    if (event.key === "ArrowDown") {
      event.preventDefault()
      setSelectedIndex((index) =>
        visibleEntries.length === 0
          ? 0
          : Math.min(index + 1, visibleEntries.length - 1),
      )
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      setSelectedIndex((index) => Math.max(index - 1, 0))
      return
    }

    if (event.key === "Enter" && visibleEntries[selectedIndex]) {
      event.preventDefault()
      runEntry(visibleEntries[selectedIndex])
    }
  }

  const emptyMessage = (() => {
    if (sectionedEntries.length > 0) {
      return null
    }
    if (searchLoading) {
      return "Searching…"
    }
    if (searchActive && searchFailed) {
      return "Search failed. Try again in a moment."
    }
    if (activeTab === "letters" && !searchActive) {
      return "Type at least two characters to search letters, questions, and responses."
    }
    return "No results found."
  })()

  function renderEntry(entry: PaletteEntry) {
    const entryIndex = visibleEntries.indexOf(entry)
    const Icon = entry.icon
    return (
      <button
        key={entry.id}
        type="button"
        data-command-index={entryIndex}
        onClick={() => runEntry(entry)}
        className={cn(
          "flex w-full items-center gap-3 rounded-md px-2 py-1.5 text-left text-sm",
          entryIndex === selectedIndex
            ? "bg-accent text-accent-foreground"
            : "text-foreground hover:bg-accent/60",
        )}
      >
        <Icon className="h-4 w-4 shrink-0 opacity-70" />
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="truncate">{entry.title}</span>
          {entry.subtitle && (
            <span className="truncate text-xs text-muted-foreground">
              {entry.subtitle}
            </span>
          )}
        </span>
        {entry.shortcut && <kbd className="shrink-0">{entry.shortcut}</kbd>}
        {entry.typeLabel && (
          <span className="shrink-0 text-xs text-muted-foreground">
            {entry.typeLabel}
          </span>
        )}
      </button>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-2xl">
        <DialogHeader className="sr-only">
          <DialogTitle>Command menu</DialogTitle>
          <DialogDescription>
            Search pages, groups, letters, and actions
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-2 border-b border-border py-2 pl-3 pr-10">
          <Input
            ref={inputRef}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setSelectedIndex(0)
              listRef.current?.scrollTo({ top: 0 })
            }}
            onKeyDown={handleInputKeyDown}
            placeholder={`Search or jump to… (${modifierKeyLabel()}K)`}
            className="h-10 border-0 bg-transparent px-1 shadow-none focus-visible:ring-0"
          />
          {searchLoading && (
            <Loader2 className="h-4 w-4 shrink-0 animate-spin text-muted-foreground" />
          )}
        </div>
        <div className="flex items-center gap-1 border-b border-border px-2 py-1.5">
          {PALETTE_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              aria-pressed={activeTab === tab.id}
              onClick={() => selectTab(tab.id)}
              className={cn(
                "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                activeTab === tab.id
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="flex flex-col">
          <div
            ref={listRef}
            className="h-[min(24rem,55dvh)] overflow-y-auto p-2"
          >
            {emptyMessage ? (
              <div className="flex items-center justify-center gap-2 px-3 py-6 text-center text-sm text-muted-foreground">
                {searchLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                <p>{emptyMessage}</p>
              </div>
            ) : (
              sectionedEntries.map(({ section, entries }) => (
                <div key={section} className="mb-2 last:mb-0">
                  <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                    {section}
                  </p>
                  {entries.map((entry) => renderEntry(entry))}
                </div>
              ))
            )}
          </div>
          {handoffEntry && (
            <div className="border-t border-border p-2">
              {renderEntry(handoffEntry)}
            </div>
          )}
          <div className="flex items-center justify-between gap-3 border-t border-border bg-muted/30 px-3 py-1.5 text-[11px] text-muted-foreground">
            <div className="hidden items-center gap-3 sm:flex">
              <span className="flex items-center gap-1">
                <kbd className="px-1 text-[10px]">↑</kbd>
                <kbd className="px-1 text-[10px]">↓</kbd>
                <span>navigate</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1 text-[10px]">↵</kbd>
                <span>open</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1 text-[10px]">tab</kbd>
                <span>switch filter</span>
              </span>
            </div>
            <button
              type="button"
              onClick={onOpenShortcutHelp}
              className="shrink-0 underline-offset-2 hover:text-foreground hover:underline"
            >
              All shortcuts
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
