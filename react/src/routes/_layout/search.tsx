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
import { useQuery } from "@tanstack/react-query"
import type { SearchHit } from "../../client"
import { performSearchSearchSearchGetOptions } from "../../client/@tanstack/react-query.gen"
import { SearchResultRow } from "../../components/Common/SearchResultRow"
import { registerSearchFocusHandler } from "../../lib/globalKeyboardShortcuts"

export const Route = createFileRoute("/_layout/search")({
  component: Search,
})

function SearchContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [submittedQuery, setSubmittedQuery] = useState("")
  const [hasSubmittedSearch, setHasSubmittedSearch] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)

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
  } = useQuery({
    ...performSearchSearchSearchGetOptions({
      query: {
        query: submittedQuery,
      },
    }),
    enabled: hasSubmittedSearch && Boolean(submittedQuery),
  })

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

  const hasResults = Boolean(searchResults?.results.length)
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
          placeholder="Search..."
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
          {isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ArrowRight className="h-4 w-4" />
          )}
        </Button>
      </div>

      {showInitialLoading && (
        <div className="flex items-center justify-center gap-2 py-12 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Searching...</span>
        </div>
      )}

      {hasSubmittedSearch && !isPending && isError && (
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
            No results found for "{submittedQuery}".
          </p>
        </div>
      )}

      {hasResults && searchResults && (
        <div className="mt-6">
          <p className="px-3 text-xs text-muted-foreground">
            {searchResults.total} result{searchResults.total === 1 ? "" : "s"}
          </p>
          <div className="mt-2 flex flex-col gap-0.5">
            {searchResults.results.map((result: SearchHit) => (
              <SearchResultRow key={result.api_identifier} result={result} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Search() {
  return <SearchContent />
}
