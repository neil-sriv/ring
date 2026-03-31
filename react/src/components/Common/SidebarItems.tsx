import { cn } from "@/lib/utils"
import { Link } from "@tanstack/react-router"
import { Home, Search, Settings, Users } from "lucide-react"

interface SidebarItemsProps {
  onClose?: () => void
}

const items = [
  { name: "Home", icon: Home, path: "/" as const },
  { name: "Groups", icon: Users, path: "/groups" as const },
  { name: "Search", icon: Search, path: "/search" as const },
  { name: "Settings", icon: Settings, path: "/settings" as const },
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
          {item.name}
        </Link>
      ))}
    </nav>
  )
}
