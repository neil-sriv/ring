import { useSuspenseQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Plus, Users } from "lucide-react"
import { Suspense, useState } from "react"
import { ErrorBoundary } from "react-error-boundary"
import type { UserLinked } from "../../client"
import { listGroupsPartiesGroupsGetOptions } from "../../client/@tanstack/react-query.gen"
import ActionsMenu from "../../components/Common/ActionsMenu"
import Navbar from "../../components/Common/Navbar"
import AddGroup from "../../components/Groups/AddGroup"

export const Route = createFileRoute("/_layout/groups")({
  component: Groups,
  loader: async ({ context }) => {
    if (!context.auth.user) {
      throw new Error("User not authenticated")
    }
    return context.auth.user
  },
})

function GroupTableBody() {
  const currentUser = Route.useLoaderData<UserLinked>()
  const { data: groups } = useSuspenseQuery({
    ...listGroupsPartiesGroupsGetOptions({
      query: { user_api_id: currentUser?.api_identifier },
    }),
  })
  const [isAddGroupOpen, setIsAddGroupOpen] = useState(false)

  if (!groups) {
    return null
  }

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
        <Users
          className="h-8 w-8 text-muted-foreground/60"
          strokeWidth={1.5}
        />
        <h3 className="mt-4 font-display text-lg font-medium">
          No groups yet
        </h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Create a group to invite friends and start a letter loop.
        </p>
        <Button className="mt-6" onClick={() => setIsAddGroupOpen(true)}>
          <Plus className="h-4 w-4" />
          Create group
        </Button>
        <AddGroup
          isOpen={isAddGroupOpen}
          onClose={() => setIsAddGroupOpen(false)}
        />
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[30%]">Name</TableHead>
          <TableHead>Members</TableHead>
          <TableHead className="w-16 text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {groups.map((group) => (
          <TableRow key={group.api_identifier}>
            <TableCell>
              <Link
                to="/groups/$groupId/loops"
                params={{ groupId: group.api_identifier }}
                className="font-medium text-foreground transition-colors hover:text-primary"
              >
                {group.name}
              </Link>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {group.members.length}{" "}
                {group.members.length === 1 ? "member" : "members"}
              </p>
            </TableCell>
            <TableCell className="whitespace-normal text-sm text-muted-foreground">
              {group.members
                .map((member) => {
                  return member.name
                })
                .sort()
                .join(", ")}
            </TableCell>
            <TableCell className="text-right">
              <ActionsMenu type={"Group"} value={group} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function GroupTable() {
  return (
    <ErrorBoundary
      fallbackRender={({ error }) => (
        <div className="rounded-lg border border-dashed px-6 py-12 text-center text-sm text-muted-foreground">
          Something went wrong: {error.message}
        </div>
      )}
    >
      <Suspense
        fallback={
          <div className="flex flex-col gap-2">
            {new Array(5).fill(null).map((_, index) => (
              <Skeleton key={index} className="h-11 w-full" />
            ))}
          </div>
        }
      >
        <GroupTableBody />
      </Suspense>
    </ErrorBoundary>
  )
}

function Groups() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
        Groups
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        The circles you write with.
      </p>
      <Navbar type={"Group"} />
      <GroupTable />
    </div>
  )
}
