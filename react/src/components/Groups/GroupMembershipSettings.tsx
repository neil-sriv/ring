import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import type { UserUnlinked } from "../../client"
import { readGroupPartiesGroupGroupApiIdGetOptions } from "../../client/@tanstack/react-query.gen"
import { userInitials } from "../../util/misc"
import RemoveMemberConfirmation from "./RemoveMemberConfirmation"

function GroupMembershipSettings({ groupId }: { groupId: string }) {
  const [memberToRemove, setMemberToRemove] = useState<UserUnlinked | null>(
    null,
  )
  // Subscribe to the group query so remove-member refetch updates this list.
  // getQueryData alone does not re-render when the cache is invalidated.
  const { data: group } = useQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupId },
    }),
  })

  if (group === undefined) {
    return null
  }

  const canRemoveMember = (member: UserUnlinked) => {
    return member.api_identifier !== group.admin.api_identifier
  }

  return (
    <>
      <div className="w-full max-w-2xl">
        <h3 className="text-base font-semibold">Group Membership</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Everyone who receives and writes this group's letters.
        </p>
        <ul className="mt-4 divide-y">
          {group.members.map((member) => {
            const isAdmin = member.api_identifier === group.admin.api_identifier
            return (
              <li
                key={member.api_identifier}
                className="flex items-center gap-3 py-3"
              >
                <Avatar>
                  <AvatarFallback>
                    {userInitials(member.name, member.email)}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium">
                      {member.name || member.email}
                    </p>
                    {isAdmin && <Badge variant="secondary">Admin</Badge>}
                  </div>
                  {member.name ? (
                    <p className="truncate text-xs text-muted-foreground">
                      {member.email}
                    </p>
                  ) : null}
                </div>
                {canRemoveMember(member) ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => setMemberToRemove(member)}
                  >
                    Remove
                  </Button>
                ) : null}
              </li>
            )
          })}
        </ul>
      </div>
      {memberToRemove ? (
        <RemoveMemberConfirmation
          groupId={groupId}
          member={memberToRemove}
          isOpen={memberToRemove !== null}
          onClose={() => setMemberToRemove(null)}
        />
      ) : null}
    </>
  )
}

export default GroupMembershipSettings
