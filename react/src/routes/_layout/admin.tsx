import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Suspense } from "react"
import type { UserLinked } from "../../client"
import { readUsersPartiesUsersGetOptions } from "../../client/@tanstack/react-query.gen"
import ActionsMenu from "../../components/Common/ActionsMenu"
import Navbar from "../../components/Common/Navbar"

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  loader: async ({ context }) => {
    if (!context.auth.user?.admin) {
      throw new Error("User is not an admin")
    }
    return context.auth.user
  },
})

const MembersTableBody = () => {
  const currentUser = Route.useLoaderData<UserLinked>()

  const { data: users } = useSuspenseQuery({
    ...readUsersPartiesUsersGetOptions(),
  })

  return (
    <TableBody>
      {users.map((user) => (
        <TableRow key={user.api_identifier}>
          <TableCell className={!user.name ? "text-muted-foreground" : ""}>
            {user.name || "N/A"}
            {currentUser?.api_identifier === user.api_identifier && (
              <Badge className="ml-1" variant="secondary">
                You
              </Badge>
            )}
          </TableCell>
          <TableCell>{user.email}</TableCell>
          {/* <TableCell>{user.is_superuser ? "Superuser" : "User"}</TableCell> */}
          {/* <TableCell>{false ? "Superuser" : "User"}</TableCell> */}
          <TableCell>{user.api_identifier}</TableCell>
          <TableCell>
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  user.is_active ? "bg-green-500" : "bg-red-500"
                }`}
              />
              {/* {user.is_active ? "Active" : "Inactive"} */}
              {user.is_active ? "Active" : "Inactive"}
            </div>
          </TableCell>
          <TableCell>
            <ActionsMenu type="User" value={user} />
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  )
}

const MembersBodySkeleton = () => {
  return (
    <TableBody>
      <TableRow>
        {new Array(5).fill(null).map((_, index) => (
          <TableCell key={index}>
            <Skeleton className="h-4 w-full my-4" />
          </TableCell>
        ))}
      </TableRow>
    </TableBody>
  )
}

function Admin() {
  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold text-center md:text-left pt-12">
        User Management
      </h2>
      <Navbar type={"User"} />
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[20%]">Full name</TableHead>
            <TableHead className="w-[50%]">Email</TableHead>
            <TableHead className="w-[10%]">API ID</TableHead>
            <TableHead className="w-[10%]">Status</TableHead>
            <TableHead className="w-[10%]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <Suspense fallback={<MembersBodySkeleton />}>
          <MembersTableBody />
        </Suspense>
      </Table>
    </div>
  )
}
