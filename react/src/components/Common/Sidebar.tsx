import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { LogOut, Menu } from "lucide-react"
import { useState } from "react"

import type { UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const [isOpen, setIsOpen] = useState(false)
  const { logout } = useAuth()

  const handleLogout = async () => {
    logout()
    queryClient.clear()
  }

  const sidebarContent = (onClose?: () => void) => (
    <div className="flex h-full flex-col justify-between">
      <div className="flex flex-col gap-1">
        <Link to="/" className="px-3 py-4" onClick={onClose}>
          <h1 className="text-lg font-semibold tracking-tight text-foreground">
            Ring
          </h1>
        </Link>
        <Separator className="mb-2" />
        <SidebarItems onClose={onClose} />
      </div>
      <div className="flex flex-col gap-2">
        <Separator />
        {currentUser?.email && (
          <p className="truncate px-3 py-1 text-xs text-muted-foreground">
            {currentUser.email}
          </p>
        )}
        <button
          onClick={handleLogout}
          className={cn(
            "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-destructive",
            "transition-colors hover:bg-destructive/10",
          )}
        >
          <LogOut className="h-4 w-4" />
          Log out
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile hamburger */}
      <Button
        variant="outline"
        size="icon"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={() => setIsOpen(true)}
      >
        <Menu className="h-4 w-4" />
        <span className="sr-only">Open menu</span>
      </Button>
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="left" className="w-60 p-4">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          {sidebarContent(() => setIsOpen(false))}
        </SheetContent>
      </Sheet>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex sticky top-0 h-screen w-60 shrink-0 flex-col border-r border-border bg-sidebar p-3">
        {sidebarContent()}
      </aside>
    </>
  )
}

export default Sidebar
