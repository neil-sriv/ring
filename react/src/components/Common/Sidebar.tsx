import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { LogOut, Menu } from "lucide-react"
import { useCallback, useState } from "react"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import { useSidebarSwipe } from "../../hooks/useSidebarSwipe"
import { userInitials } from "../../util/misc"
import NotificationBell from "./NotificationBell"
import { RingMark } from "./RingMark"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const [isOpen, setIsOpen] = useState(false)
  const { logout } = useAuth()

  const openSidebar = useCallback(() => setIsOpen(true), [])
  const closeSidebar = useCallback(() => setIsOpen(false), [])

  useSidebarSwipe({ isOpen, onOpen: openSidebar, onClose: closeSidebar })

  const handleLogout = async () => {
    logout()
    queryClient.clear()
  }

  const sidebarContent = (onClose?: () => void) => (
    <div className="flex h-full flex-col">
      <Link
        to="/"
        className="mx-1 mb-4 mt-1 flex items-center gap-2 rounded-md px-1.5 py-1"
        onClick={onClose}
      >
        <RingMark className="h-5 w-5 shrink-0 text-primary" />
        <span className="font-display text-xl font-semibold tracking-tight text-sidebar-accent-foreground">
          Ring
        </span>
      </Link>
      <SidebarItems onClose={onClose} />
      <div className="mt-auto">
        <div className="flex items-center gap-2 border-t border-sidebar-border px-1.5 pb-1 pt-3">
          <Avatar className="h-7 w-7">
            <AvatarFallback>
              {userInitials(currentUser?.name, currentUser?.email)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            {currentUser?.name && (
              <p className="truncate text-xs font-medium text-sidebar-foreground">
                {currentUser.name}
              </p>
            )}
            <p className="truncate text-[0.6875rem] text-sidebar-foreground/60">
              {currentUser?.email}
            </p>
          </div>
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-md p-1.5 text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-destructive"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="sr-only">Log out</span>
                </button>
              </TooltipTrigger>
              <TooltipContent side="top">Log out</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex h-12 shrink-0 items-center gap-1 border-b border-sidebar-border bg-sidebar px-2 md:hidden">
        <Button variant="ghost" size="icon" onClick={openSidebar}>
          <Menu className="h-4 w-4" />
          <span className="sr-only">Open menu</span>
        </Button>
        <Link
          to="/"
          className="flex items-center gap-2 rounded-md px-1.5 py-1 font-display text-lg font-semibold tracking-tight text-sidebar-accent-foreground"
        >
          <RingMark className="h-[1.125rem] w-[1.125rem] shrink-0 text-primary" />
          Ring
        </Link>
        <NotificationBell className="ml-auto" />
      </header>
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="left" className="w-60 bg-sidebar p-3">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          {sidebarContent(closeSidebar)}
        </SheetContent>
      </Sheet>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex sticky top-0 h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar p-3">
        {sidebarContent()}
      </aside>
    </>
  )
}

export default Sidebar
