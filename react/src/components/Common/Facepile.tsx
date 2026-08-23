import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { UserUnlinked } from "../../client"

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) {
    return "?"
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function Facepile({
  users,
  max = 4,
  className,
}: {
  users: UserUnlinked[]
  max?: number
  className?: string
}): JSX.Element | null {
  if (users.length === 0) {
    return null
  }
  const visible = users.slice(0, max)
  const overflowCount = users.length - visible.length

  return (
    <div
      role="group"
      aria-label={users.map((user) => user.name).join(", ")}
      className={cn("flex items-center -space-x-2", className)}
    >
      {visible.map((user) => (
        <Avatar
          key={user.api_identifier}
          title={user.name}
          className="h-6 w-6 ring-2 ring-card"
        >
          <AvatarFallback className="text-xs">
            {getInitials(user.name)}
          </AvatarFallback>
        </Avatar>
      ))}
      {overflowCount > 0 && (
        <span
          title={users
            .slice(max)
            .map((user) => user.name)
            .join(", ")}
          className="flex h-6 w-6 select-none items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground ring-2 ring-card"
        >
          +{overflowCount}
        </span>
      )}
    </div>
  )
}
