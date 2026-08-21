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
          <TableCell>
            <div className="flex items-center gap-2">
              <span
                className={
                  user.name ? "font-medium" : "text-muted-foreground"
                }
              >
                {user.name || "N/A"}
              </span>
              {currentUser?.api_identifier === user.api_identifier && (
                <Badge variant="secondary">You</Badge>
              )}
            </div>
          </TableCell>
          <TableCell>{user.email}</TableCell>
          <TableCell className="font-mono text-xs text-muted-foreground">
            {user.api_identifier}
          </TableCell>
          <TableCell>
            <Badge variant="success">Active</Badge>
          </TableCell>
          <TableCell className="text-right">
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
      {new Array(5).fill(null).map((_, rowIndex) => (
        <TableRow key={rowIndex}>
          {new Array(5).fill(null).map((_, cellIndex) => (
            <TableCell key={cellIndex}>
              <Skeleton className="h-4 w-full" />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </TableBody>
  )
}

function Admin() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
        Admin
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Manage everyone with a Ring account.
      </p>
      <Navbar type={"User"} />
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[20%]">Full name</TableHead>
            <TableHead className="w-[30%]">Email</TableHead>
            <TableHead className="w-[30%]">API ID</TableHead>
            <TableHead className="w-[10%]">Status</TableHead>
            <TableHead className="w-[10%] text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <Suspense fallback={<MembersBodySkeleton />}>
          <MembersTableBody />
        </Suspense>
      </Table>
    </div>
  )
}
