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
import { useQuery, useQueryClient } from "@tanstack/react-query"
import type { SearchSort, UserLinked } from "../../client"
import {
  performSearchSearchSearchGetOptions,
  readGroupPartiesGroupGroupApiIdGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { SearchFilters } from "../../components/Common/SearchFilters"
import { SearchResultRow } from "../../components/Common/SearchResultRow"

export const Route = createFileRoute("/_layout/search")({
  component: Search,
})

function SearchContent() {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const groups = currentUser?.groups ?? []

  const [searchQuery, setSearchQuery] = useState("")
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null)
  const [groupApiId, setGroupApiId] = useState<string | undefined>()
  const [participantApiId, setParticipantApiId] = useState<string | undefined>()
  const [sort, setSort] = useState<SearchSort>("relevance")

  const { data: selectedGroup } = useQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupApiId ?? "" },
    }),
    enabled: Boolean(groupApiId),
  })

  const {
    data: searchResults,
    isFetching,
    refetch,
  } = useQuery({
    ...performSearchSearchSearchGetOptions({
      query: {
        query: submittedQuery ?? "",
        group_api_id: groupApiId ?? null,
        participant_api_id: participantApiId ?? null,
        sort,
        limit: 25,
      },
    }),
    enabled: Boolean(submittedQuery?.trim()),
  })

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    if (submittedQuery === searchQuery) {
      await refetch()
      return
    }
    setSubmittedQuery(searchQuery)
  }

  const showTimestamp = sort !== "relevance"
  const hasSearched = submittedQuery !== null

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
                void handleSearch()
              }
            }}
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => void handleSearch()}
            className="absolute right-1 top-1/2 -translate-y-1/2"
            disabled={isFetching}
          >
            {isFetching ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <SearchIcon className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>

      <SearchFilters
        groups={groups}
        members={selectedGroup?.members ?? []}
        groupApiId={groupApiId}
        participantApiId={participantApiId}
        sort={sort}
        onGroupChange={setGroupApiId}
        onParticipantChange={setParticipantApiId}
        onSortChange={setSort}
      />

      {hasSearched && (
        <div className="px-4 overflow-auto">
          {isFetching && !searchResults ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : searchResults && searchResults.results.length > 0 ? (
            <>
              <p className="text-sm text-muted-foreground pb-4">
                {searchResults.total} result
                {searchResults.total === 1 ? "" : "s"}
              </p>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {searchResults.results.map((result) => (
                    <SearchResultRow
                      key={`${result.type}-${result.model.api_identifier}`}
                      result={result}
                      showTimestamp={showTimestamp}
                    />
                  ))}
                </TableBody>
              </Table>
            </>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No results found.
            </p>
          )}
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
