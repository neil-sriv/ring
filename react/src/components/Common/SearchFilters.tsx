import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown } from "lucide-react"
import type { ReactNode } from "react"

import type { GroupUnlinked, SearchSort, UserUnlinked } from "../../client"

interface SearchFiltersProps {
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

interface FilterMenuProps {
  label: string
  value: string
  active: boolean
  disabled?: boolean
  children: ReactNode
}

function FilterMenu({
  label,
  value,
  active,
  disabled,
  children,
}: FilterMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={active ? "secondary" : "outline"}
          size="sm"
          disabled={disabled}
          aria-label={label}
          className={
            active
              ? "h-7 justify-between gap-1.5 rounded-full px-3 text-xs"
              : "h-7 justify-between gap-1.5 rounded-full px-3 text-xs text-muted-foreground"
          }
        >
          {value}
          <ChevronDown className="h-3 w-3 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="start"
        className="max-h-72 w-56 overflow-y-auto"
      >
        {children}
      </DropdownMenuContent>
    </DropdownMenu>
  )
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
    <div className="mt-3 flex flex-wrap items-center gap-1.5">
      <FilterMenu
        label="Group"
        value={
          selectedGroup?.name ?? (groupApiId ? "Selected group" : "All groups")
        }
        active={Boolean(groupApiId)}
      >
        <DropdownMenuItem
          onClick={() => {
            onGroupChange(undefined)
          }}
        >
          All groups
        </DropdownMenuItem>
        {groups.map((group) => (
          <DropdownMenuItem
            key={group.api_identifier}
            onClick={() => {
              onGroupChange(group.api_identifier)
            }}
          >
            {group.name}
          </DropdownMenuItem>
        ))}
      </FilterMenu>

      <FilterMenu
        label="Responder"
        value={
          selectedParticipant?.name ||
          selectedParticipant?.email ||
          (participantApiId ? "Selected responder" : "All responders")
        }
        active={Boolean(participantApiId)}
        disabled={!groupApiId}
      >
        <DropdownMenuItem onClick={() => onParticipantChange(undefined)}>
          All responders
        </DropdownMenuItem>
        {members.map((member) => (
          <DropdownMenuItem
            key={member.api_identifier}
            onClick={() => onParticipantChange(member.api_identifier)}
          >
            {member.name || member.email}
          </DropdownMenuItem>
        ))}
      </FilterMenu>

      <FilterMenu
        label="Sort"
        value={SORT_LABELS[sort]}
        active={sort !== "relevance"}
      >
        {(Object.keys(SORT_LABELS) as SearchSort[]).map((sortOption) => (
          <DropdownMenuItem
            key={sortOption}
            onClick={() => onSortChange(sortOption)}
          >
            {SORT_LABELS[sortOption]}
          </DropdownMenuItem>
        ))}
      </FilterMenu>
    </div>
  )
}
