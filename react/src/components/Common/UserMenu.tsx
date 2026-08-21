import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { LogOut, User } from "lucide-react"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import useAuth from "../../hooks/useAuth"
import { userInitials } from "../../util/misc"

const UserMenu = () => {
  const queryClient = useQueryClient()
  const { logout } = useAuth()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )

  const handleLogout = async () => {
    logout()
    queryClient.clear()
  }

  return (
    <div className="hidden md:block fixed top-4 right-4 z-40">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="cursor-pointer rounded-full transition-shadow focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/30 hover:ring-[3px] hover:ring-ring/20"
          >
            <Avatar>
              <AvatarFallback>
                {userInitials(currentUser?.name, currentUser?.email)}
              </AvatarFallback>
            </Avatar>
            <span className="sr-only">User menu</span>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="font-normal">
            <p className="truncate text-sm font-medium text-foreground">
              {currentUser?.name}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {currentUser?.email}
            </p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link
              to="/settings"
              className="flex items-center gap-2 cursor-pointer"
            >
              <User className="h-4 w-4" />
              My profile
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={handleLogout}
            className="text-destructive focus:text-destructive cursor-pointer [&>svg]:text-destructive"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

export default UserMenu
