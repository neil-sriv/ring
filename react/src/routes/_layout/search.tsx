import { createFileRoute } from "@tanstack/react-router"
import {
  ArrowRight,
  Loader2,
  Search as SearchIcon,
  SearchX,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useInfiniteQuery } from "@tanstack/react-query"
import type { SearchHit, SearchableType } from "../../client"
import { performSearchSearchSearchGetInfiniteOptions } from "../../client/@tanstack/react-query.gen"
import { SearchResultRow } from "../../components/Common/SearchResultRow"
import { registerSearchFocusHandler } from "../../lib/globalKeyboardShortcuts"

export const Route = createFileRoute("/_layout/search")({
  component: Search,
})

const SEARCH_PAGE_SIZE = 10

const SEARCH_TYPE_FILTERS: { value: SearchableType; label: string }[] = [
  { value: "group", label: "Groups" },
  { value: "user", label: "Users" },
  { value: "question", label: "Questions" },
  { value: "response", label: "Responses" },
  { value: "letter", label: "Letters" },
]

function SearchContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [submittedQuery, setSubmittedQuery] = useState("")
  const [hasSubmittedSearch, setHasSubmittedSearch] = useState(false)
  const [selectedTypes, setSelectedTypes] = useState<SearchableType[]>([])
  const searchInputRef = useRef<HTMLInputElement>(null)
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const toggleType = (type: SearchableType) => {
    setSelectedTypes((current) =>
      current.includes(type)
        ? current.filter((selected) => selected !== type)
        : [...current, type],
    )
  }

  // Sorted copy so the query key (and cache entry) is independent of the
  // order the chips were toggled in.
  const activeTypes = [...selectedTypes].sort()

  useEffect(() => {
    searchInputRef.current?.focus()
    registerSearchFocusHandler(() => searchInputRef.current?.focus())
    return () => registerSearchFocusHandler(null)
  }, [])

  const {
    data: searchResults,
    error,
    isError,
    isFetching,
    isPending,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isFetchNextPageError,
  } = useInfiniteQuery({
    ...performSearchSearchSearchGetInfiniteOptions({
      query: {
        query: submittedQuery,
        limit: SEARCH_PAGE_SIZE,
        ...(activeTypes.length > 0 ? { types: activeTypes } : {}),
      },
    }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      // A partial page means the results are exhausted; otherwise the next
      // offset is the number of results loaded so far.
      if (lastPage.results.length < SEARCH_PAGE_SIZE) {
        return undefined
      }
      return allPages.reduce((count, page) => count + page.results.length, 0)
    },
    enabled: hasSubmittedSearch && Boolean(submittedQuery),
  })

  const searchHits = searchResults?.pages.flatMap((page) => page.results) ?? []

  // Auto-fetch the next page when the sentinel below the results scrolls
  // into view (within 200px of the viewport). Gated on isError so a failed
  // page fetch doesn't re-arm the observer and hammer retries while the
  // sentinel is still in view; recovery goes through the explicit retry
  // button instead.
  useEffect(() => {
    const sentinel = loadMoreRef.current
    if (!sentinel || !hasNextPage || isFetchingNextPage || isError) {
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          fetchNextPage()
        }
      },
      { rootMargin: "200px" },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, isError, fetchNextPage])

  const handleSearch = async () => {
    const trimmedQuery = searchQuery.trim()
    if (!trimmedQuery) {
      return
    }
    setHasSubmittedSearch(true)
    if (trimmedQuery === submittedQuery) {
      await refetch()
      return
    }
    setSubmittedQuery(trimmedQuery)
  }

  const hasResults = searchHits.length > 0
  const showInitialLoading = hasSubmittedSearch && isPending
  const hasEmptyResults =
    hasSubmittedSearch && !isPending && !isError && !hasResults

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
        Search
      </h1>
      <div className="relative mt-6">
        <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={searchInputRef}
          type="text"
          placeholder="Search… author:name status:open"
          className="h-11 pl-10 pr-12"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSearch()
            }
          }}
        />
        <Button
          variant="ghost"
          size="icon"
          onClick={handleSearch}
          disabled={!searchQuery.trim()}
          className="absolute right-1 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          {isFetching && !isFetchingNextPage ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ArrowRight className="h-4 w-4" />
          )}
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        GitHub-style filters: <span className="font-mono">author:jane</span>,{" "}
        <span className="font-mono">status:open</span>,{" "}
        <span className="font-mono">status:published</span>,{" "}
        <span className="font-mono">author:@me</span>
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {SEARCH_TYPE_FILTERS.map(({ value, label }) => {
          const isSelected = selectedTypes.includes(value)
          return (
            <Button
              key={value}
              variant={isSelected ? "secondary" : "outline"}
              size="sm"
              aria-pressed={isSelected}
              onClick={() => toggleType(value)}
              className={
                isSelected
                  ? "h-7 rounded-full px-3 text-xs"
                  : "h-7 rounded-full px-3 text-xs text-muted-foreground"
              }
            >
              {label}
            </Button>
          )
        })}
        {selectedTypes.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedTypes([])}
            className="h-7 rounded-full px-2 text-xs text-muted-foreground"
          >
            Clear
          </Button>
        )}
      </div>

      {showInitialLoading && (
        <div className="flex items-center justify-center gap-2 py-12 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Searching...</span>
        </div>
      )}

      {hasSubmittedSearch && !isPending && isError && !isFetchNextPageError && (
        <div className="mt-6 text-sm text-destructive">
          Search failed
          {error instanceof Error && error.message ? `: ${error.message}` : "."}
        </div>
      )}

      {hasEmptyResults && (
        <div className="mt-6 flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
          <SearchX
            className="h-8 w-8 text-muted-foreground/60"
            strokeWidth={1.5}
          />
          <h3 className="mt-4 font-display text-lg font-medium">No results</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            No results found for "{submittedQuery}"
            {selectedTypes.length > 0 ? " with the selected filters" : ""}.
          </p>
        </div>
      )}

      {hasResults && (
        <div className="mt-6">
          <p className="px-3 text-xs text-muted-foreground">
            {searchHits.length}
            {hasNextPage ? "+" : ""} result
            {searchHits.length === 1 && !hasNextPage ? "" : "s"}
          </p>
          <div className="mt-2 flex flex-col gap-0.5">
            {searchHits.map((result: SearchHit) => (
              <SearchResultRow key={result.api_identifier} result={result} />
            ))}
          </div>
          <div ref={loadMoreRef} aria-hidden="true" />
          {isFetchingNextPage && (
            <div className="flex items-center justify-center gap-2 py-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading more...</span>
            </div>
          )}
          {isFetchNextPageError && !isFetchingNextPage && (
            <div className="flex items-center justify-center gap-3 py-4 text-sm text-muted-foreground">
              <span>Couldn't load more results.</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchNextPage()}
              >
                Retry
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Search() {
  return <SearchContent />
}
