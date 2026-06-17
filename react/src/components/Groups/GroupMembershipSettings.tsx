import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import type { GroupLinked, UserUnlinked } from "../../client"
import { readGroupPartiesGroupGroupApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen"
import RemoveMemberConfirmation from "./RemoveMemberConfirmation"

function GroupMembershipSettings({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient()
  const [memberToRemove, setMemberToRemove] = useState<UserUnlinked | null>(
    null,
  )
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    }),
  )

  if (group === undefined) {
    return null
  }

  const canRemoveMember = (member: UserUnlinked) => {
    return member.api_identifier !== group.admin.api_identifier
  }

  return (
    <>
      <div className="w-full">
        <h3 className="text-sm font-semibold py-4">Group Membership</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {group.members.map((member) => {
              const isAdmin = member.api_identifier === group.admin.api_identifier
              return (
                <TableRow key={member.api_identifier}>
                  <TableCell>{member.name}</TableCell>
                  <TableCell>{member.email}</TableCell>
                  <TableCell>{isAdmin ? "Admin" : "Member"}</TableCell>
                  <TableCell>
                    {canRemoveMember(member) ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setMemberToRemove(member)}
                      >
                        Remove
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
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
