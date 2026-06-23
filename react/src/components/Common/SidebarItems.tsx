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
    <nav className="flex flex-col gap-0.5">
      {items.map((item) => (
        <Link
          key={item.name}
          to={item.path}
          onClick={onClose}
          className={cn(
            "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-foreground/70",
            "transition-colors hover:bg-accent hover:text-accent-foreground",
          )}
          activeProps={{
            className: "bg-accent text-accent-foreground font-semibold",
          }}
        >
          <item.icon className="h-4 w-4 shrink-0" />
          <span className="flex-1">{item.name}</span>
          <kbd className="hidden text-[10px] font-mono text-muted-foreground lg:inline">
            {item.shortcut}
          </kbd>
        </Link>
      ))}
    </nav>
  )
}
