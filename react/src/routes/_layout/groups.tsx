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
import { Plus } from "lucide-react"
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
      <TableBody>
        <TableRow>
          <TableCell colSpan={3} className="hover:bg-transparent">
            <div className="text-center py-12 w-full">
              <div className="flex flex-col items-center gap-4 px-4">
                <p className="text-lg text-foreground">No groups yet</p>
                <p className="text-sm text-muted-foreground max-w-md">
                  Create a group to invite friends and start a letter loop.
                </p>
                <Button
                  onClick={() => setIsAddGroupOpen(true)}
                  className="gap-1"
                >
                  <Plus className="h-4 w-4" />
                  Create a group
                </Button>
              </div>
              <AddGroup
                isOpen={isAddGroupOpen}
                onClose={() => setIsAddGroupOpen(false)}
              />
            </div>
          </TableCell>
        </TableRow>
      </TableBody>
    )
  }

  return (
    <>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Members</TableHead>
          {/* <TableHead>Letters</TableHead> */}
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {groups.map((group) => (
          <TableRow key={group.api_identifier}>
            {/* <TableCell>{group.name}</TableCell> */}
            <TableCell>
              <Link
                to="/groups/$groupId/loops"
                params={{ groupId: group.api_identifier }}
                className="underline"
              >
                {group.name}
              </Link>
            </TableCell>
            <TableCell className="whitespace-normal">
              <div>
                <p>
                  {group.members
                    .map((member) => {
                      return member.name
                    })
                    .sort()
                    .join(", ")}
                </p>
              </div>
            </TableCell>
            {/* <TableCell>
              {group.letters
                .map((letter) => {
                  return letter.number;
                })
                .sort()
                .join(", ")}
            </TableCell> */}
            <TableCell>
              <ActionsMenu type={"Group"} value={group} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </>
  )
}

function GroupTable() {
  return (
    <Table>
      <ErrorBoundary
        fallbackRender={({ error }) => (
          <TableBody>
            <TableRow>
              <TableCell colSpan={4}>
                Something went wrong: {error.message}
              </TableCell>
            </TableRow>
          </TableBody>
        )}
      >
        <Suspense
          fallback={
            <TableBody>
              {new Array(5).fill(null).map((_, index) => (
                <TableRow key={index}>
                  {new Array(4).fill(null).map((_, index) => (
                    <TableCell key={index}>
                      <div className="flex">
                        <Skeleton className="h-5 w-5" />
                      </div>
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          }
        >
          <GroupTableBody />
        </Suspense>
      </ErrorBoundary>
    </Table>
  )
}

function Groups() {
  return (
    <div className="max-w-screen-xl mx-auto px-4">
      <h2 className="text-2xl font-bold text-center md:text-left pt-12">
        Groups
      </h2>

      <Navbar type={"Group"} />
      <GroupTable />
    </div>
  )
}
