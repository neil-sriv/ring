import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useQueryClient } from "@tanstack/react-query"

import type { GroupLinked } from "../../client"
import { readGroupPartiesGroupGroupApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen"

function GroupMembershipSettings({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient()
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    }),
  )

  if (group === undefined) {
    return null
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {group.members.map((member) => {
              return (
                <TableRow key={member.email}>
                  <TableCell>{member.name}</TableCell>
                  <TableCell>{member.email}</TableCell>
                  <TableCell>Member</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </>
  )
}

export default GroupMembershipSettings
