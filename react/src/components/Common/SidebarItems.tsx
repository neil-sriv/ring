import { cn } from "@/lib/utils"
import { Link } from "@tanstack/react-router"
import { Home, Search, Settings, Users } from "lucide-react"

interface SidebarItemsProps {
  onClose?: () => void
}

const items = [
  { name: "Home", icon: Home, path: "/" as const, shortcut: "g h" },
  { name: "Groups", icon: Users, path: "/groups" as const, shortcut: "g g" },
  { name: "Search", icon: Search, path: "/search" as const, shortcut: "g s" },
  {
    name: "Settings",
    icon: Settings,
    path: "/settings" as const,
    shortcut: "g p",
  },
]

export default function SidebarItems({ onClose }: SidebarItemsProps) {
  return (
    <nav className="flex flex-col gap-px">
      {items.map((item) => (
        <Link
          key={item.name}
          to={item.path}
          onClick={onClose}
          className={cn(
            "group flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium text-sidebar-foreground/75",
            "transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground",
            "data-[status=active]:bg-sidebar-accent data-[status=active]:font-semibold data-[status=active]:text-sidebar-accent-foreground",
          )}
        >
          <item.icon className="h-4 w-4 shrink-0 text-sidebar-foreground/50 transition-colors group-hover:text-sidebar-foreground/80 group-data-[status=active]:text-sidebar-accent-foreground" />
          <span className="flex-1">{item.name}</span>
          <kbd className="hidden border-none bg-transparent px-0 text-[0.625rem] text-sidebar-foreground/40 shadow-none lg:inline">
            {item.shortcut}
          </kbd>
        </Link>
      ))}
    </nav>
  )
}
