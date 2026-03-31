import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { LogOut, User, UserCircle } from "lucide-react"

import useAuth from "../../hooks/useAuth"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const UserMenu = () => {
  const queryClient = useQueryClient()
  const { logout } = useAuth()

  const handleLogout = async () => {
    logout()
    queryClient.clear()
  }

  return (
    <div className="hidden md:block fixed top-4 right-4 z-40">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="default"
            size="icon"
            className="rounded-full"
          >
            <UserCircle className="h-5 w-5" />
            <span className="sr-only">User menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem asChild>
            <Link to="/settings" className="flex items-center gap-2 cursor-pointer">
              <User className="h-4 w-4" />
              My profile
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={handleLogout}
            className="text-destructive focus:text-destructive cursor-pointer"
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
