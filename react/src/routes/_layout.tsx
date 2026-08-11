import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"

import { useQueryClient } from "@tanstack/react-query"
import {
  listDashboardLettersLettersLettersDashboardGetOptions,
  readUserMePartiesMeGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../client/@tanstack/react-query.gen"
import type { UserLinked } from "../client/types.gen"
import { KeyboardShortcuts } from "../components/Common/KeyboardShortcuts"
import Sidebar from "../components/Common/Sidebar"
import UserMenu from "../components/Common/UserMenu"
import { subscribeToPush } from "../util/notifications"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async ({ context, location }): Promise<void> => {
    try {
      const user = await context.queryClient.ensureQueryData({
        ...readUserMePartiesMeGetOptions(),
      })
      context.auth.user = user
      void context.queryClient.prefetchQuery({
        ...listDashboardLettersLettersLettersDashboardGetOptions(),
      })
    } catch (error) {
      // If authentication fails, redirect to login with the current path as next parameter
      // Only add next parameter if we're not already on the login page
      if (location.pathname !== "/login") {
        const hash = typeof window !== "undefined" ? window.location.hash : ""
        const currentPath = location.pathname + location.searchStr + hash
        throw redirect({
          to: "/login",
          search: {
            next: currentPath,
          },
        })
      }
      // Already on login page, just redirect without next parameter
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const userApiId = currentUser?.api_identifier
  const isLoading = false

  useEffect(() => {
    if (!userApiId) {
      return
    }
    const subscribe = () => {
      void subscribeToPush(userApiId)
    }
    if ("requestIdleCallback" in window) {
      const idleId = window.requestIdleCallback(subscribe)
      return () => window.cancelIdleCallback(idleId)
    }
    const timeoutId = setTimeout(subscribe, 0)
    return () => clearTimeout(timeoutId)
  }, [userApiId])

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      {isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      )}
      <UserMenu />
      <KeyboardShortcuts />
    </div>
  )
}
