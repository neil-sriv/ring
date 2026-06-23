import { createFileRoute } from "@tanstack/react-router"
import { Loader2, Search as SearchIcon } from "lucide-react"
import { Suspense, useState } from "react"

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
import type { SearchResult } from "../../client"
import { performSearchSearchSearchGetOptions } from "../../client/@tanstack/react-query.gen"
import { SearchResultRow } from "../../components/Common/SearchResultRow"

export const Route = createFileRoute("/_layout/search")({
  component: Search,
})

function SearchContent() {
  const [searchQuery, setSearchQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)

  const { data: searchResults, refetch } = useQuery({
    ...performSearchSearchSearchGetOptions({
      query: {
        query: searchQuery,
      },
    }),
    enabled: false,
  })

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setIsSearching(true)
    await refetch()
  }

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold text-center md:text-left pt-12 px-4">
        Search
      </h2>
      <div className="flex py-8 px-4">
        <div className="relative w-full">
          <Input
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
            className="absolute right-1 top-1/2 -translate-y-1/2"
          >
            <SearchIcon className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {isSearching && searchResults && (
        <div className="px-4 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {searchResults.results.map((result: SearchResult, index) => (
                <SearchResultRow
                  key={
                    "api_identifier" in result.model
                      ? `${result.type}:${result.model.api_identifier}`
                      : `${result.type}:${index}`
                  }
                  result={result}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

function Search() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  )
}
