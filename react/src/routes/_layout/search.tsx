import { createFileRoute } from "@tanstack/react-router"
import { Loader2, Search as SearchIcon } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
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
    <div className="w-full">
      <h2 className="text-2xl font-bold text-center md:text-left pt-12 px-4">
        Search
      </h2>
      <div className="flex py-8 px-4">
        <div className="relative w-full">
          <Input
            ref={searchInputRef}
            type="text"
            placeholder="Search..."
            className="h-12 pr-12"
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
            className="absolute right-1 top-1/2 -translate-y-1/2"
          >
            {isFetching ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <SearchIcon className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>

      {showInitialLoading && (
        <div className="flex justify-center items-center gap-2 p-8 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Searching...</span>
        </div>
      )}

      {hasSubmittedSearch && !isPending && isError && (
        <div className="px-4 text-sm text-destructive">
          Search failed
          {error instanceof Error && error.message ? `: ${error.message}` : "."}
        </div>
      )}

      {hasEmptyResults && (
        <div className="px-4 text-sm text-muted-foreground">
          No results found for "{submittedQuery}".
        </div>
      )}

      {hasResults && searchResults && (
        <div className="px-4 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {searchResults.results.map((result: SearchHit) => (
                <SearchResultRow key={result.api_identifier} result={result} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

function Search() {
  return <SearchContent />
}
