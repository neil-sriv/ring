import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown } from "lucide-react"

import type { GroupUnlinked, SearchSort, UserUnlinked } from "../../client"

type SearchFiltersProps = {
  groups: GroupUnlinked[]
  members: UserUnlinked[]
  groupApiId?: string
  participantApiId?: string
  sort: SearchSort
  onGroupChange: (groupApiId?: string) => void
  onParticipantChange: (participantApiId?: string) => void
  onSortChange: (sort: SearchSort) => void
}

const SORT_LABELS: Record<SearchSort, string> = {
  relevance: "Relevance",
  created_at_desc: "Newest first",
  created_at_asc: "Oldest first",
}

export function SearchFilters({
  groups,
  members,
  groupApiId,
  participantApiId,
  sort,
  onGroupChange,
  onParticipantChange,
  onSortChange,
}: SearchFiltersProps) {
  const selectedGroup = groups.find(
    (group) => group.api_identifier === groupApiId,
  )
  const selectedParticipant = members.find(
    (member) => member.api_identifier === participantApiId,
  )

  return (
    <div className="flex flex-wrap gap-3 px-4 pb-4">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="min-w-40 justify-between">
            {selectedGroup?.name ?? "All groups"}
            <ChevronDown className="h-4 w-4 opacity-60" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuItem
            onClick={() => {
              onGroupChange(undefined)
              onParticipantChange(undefined)
            }}
          >
            All groups
          </DropdownMenuItem>
          {groups.map((group) => (
            <DropdownMenuItem
              key={group.api_identifier}
              onClick={() => {
                onGroupChange(group.api_identifier)
                onParticipantChange(undefined)
              }}
            >
              {group.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            className="min-w-40 justify-between"
            disabled={!groupApiId}
          >
            {selectedParticipant?.name ?? "All responders"}
            <ChevronDown className="h-4 w-4 opacity-60" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuItem onClick={() => onParticipantChange(undefined)}>
            All responders
          </DropdownMenuItem>
          {members.map((member) => (
            <DropdownMenuItem
              key={member.api_identifier}
              onClick={() => onParticipantChange(member.api_identifier)}
            >
              {member.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="min-w-40 justify-between">
            {SORT_LABELS[sort]}
            <ChevronDown className="h-4 w-4 opacity-60" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          {(Object.keys(SORT_LABELS) as SearchSort[]).map((sortOption) => (
            <DropdownMenuItem
              key={sortOption}
              onClick={() => onSortChange(sortOption)}
            >
              {SORT_LABELS[sortOption]}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
