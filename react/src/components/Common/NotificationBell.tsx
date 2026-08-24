import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Bell, CheckCheck, Loader2, X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  type Notification,
  deleteNotificationNotificationsNotificationApiIdDelete,
  markAllNotificationsReadNotificationsReadAllPost,
  markNotificationReadNotificationsNotificationApiIdReadPost,
} from "../../client"
import {
  getUnreadCountNotificationsUnreadCountGetOptions,
  listNotificationsNotificationsGetOptions,
} from "../../client/@tanstack/react-query.gen"
import { cn } from "../../lib/utils"
import { formatTimeAgo } from "../../util/misc"
import { notificationTypeMeta } from "../../util/notificationDisplay"
import { notificationTargetPath } from "../../util/notifications"

// Poll lightly so push-less sessions still see fresh counts.
const UNREAD_POLL_INTERVAL_MS = 60_000

interface NotificationBellProps {
  className?: string
}

const NotificationBell = ({ className }: NotificationBellProps) => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  // Build query options per render (not at module scope): the generated
  // helpers capture the axios client's baseURL when called, and the client
  // is only configured in main.tsx after modules are imported.
  const LIST_QUERY = listNotificationsNotificationsGetOptions({
    query: { limit: 30 },
  })
  const UNREAD_QUERY = getUnreadCountNotificationsUnreadCountGetOptions()

  const { data: unreadData } = useQuery({
    ...UNREAD_QUERY,
    refetchInterval: UNREAD_POLL_INTERVAL_MS,
  })
  const unreadCount = unreadData?.unread_count ?? 0

  const { data: listData, isLoading } = useQuery({
    ...LIST_QUERY,
    enabled: isOpen,
  })
  const notifications = listData?.notifications ?? []

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: LIST_QUERY.queryKey })
    void queryClient.invalidateQueries({ queryKey: UNREAD_QUERY.queryKey })
  }

  const markReadMutation = useMutation({
    mutationFn: async (notificationApiId: string) => {
      await markNotificationReadNotificationsNotificationApiIdReadPost({
        path: { notification_api_id: notificationApiId },
        throwOnError: true,
      })
    },
    onSettled: invalidate,
  })

  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      await markAllNotificationsReadNotificationsReadAllPost({
        throwOnError: true,
      })
    },
    onSettled: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: async (notificationApiId: string) => {
      await deleteNotificationNotificationsNotificationApiIdDelete({
        path: { notification_api_id: notificationApiId },
        throwOnError: true,
      })
    },
    onSettled: invalidate,
  })

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read_at) {
      markReadMutation.mutate(notification.api_identifier)
    }
    setIsOpen(false)
    const target = notificationTargetPath(notification.target_api_id)
    if (target) {
      void navigate({ to: target.to, params: target.params })
    }
  }

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            "relative rounded-full p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/30",
            className,
          )}
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[0.625rem] font-semibold leading-none text-primary-foreground">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
          <span className="sr-only">
            Notifications{unreadCount > 0 ? ` (${unreadCount} unread)` : ""}
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-80 p-0 sm:w-96"
        onCloseAutoFocus={(event) => event.preventDefault()}
      >
        <div className="flex items-center justify-between border-b px-3 py-2">
          <p className="text-sm font-semibold">Notifications</p>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2 text-xs text-muted-foreground"
              disabled={markAllReadMutation.isPending}
              onClick={() => markAllReadMutation.mutate()}
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Mark all read
            </Button>
          )}
        </div>
        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-4 py-10 text-center">
              <Bell className="h-6 w-6 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                No notifications yet
              </p>
              <p className="text-xs text-muted-foreground/70">
                Letter updates and group activity will show up here.
              </p>
            </div>
          ) : (
            <ul>
              {notifications.map((notification) => {
                const meta = notificationTypeMeta(notification.type)
                return (
                  <li
                    key={notification.api_identifier}
                    className="group relative border-b last:border-b-0"
                  >
                    <button
                      type="button"
                      onClick={() => handleNotificationClick(notification)}
                      className="flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-accent/60"
                    >
                      <span
                        className={cn(
                          "mt-3 h-2 w-2 shrink-0 rounded-full",
                          notification.read_at
                            ? "bg-transparent"
                            : "bg-primary",
                        )}
                      />
                      <span
                        className={cn(
                          "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                          notification.read_at
                            ? "bg-muted text-muted-foreground/60"
                            : meta.accentClassName,
                        )}
                      >
                        <meta.icon className="h-3.5 w-3.5" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span
                          className={cn(
                            "block truncate text-sm",
                            notification.read_at
                              ? "text-muted-foreground"
                              : "font-medium text-foreground",
                          )}
                        >
                          {notification.title}
                        </span>
                        {notification.body && (
                          <span className="mt-0.5 line-clamp-2 block text-xs text-muted-foreground">
                            {notification.body}
                          </span>
                        )}
                        <span className="mt-0.5 block text-[0.6875rem] text-muted-foreground/70">
                          {formatTimeAgo(notification.created_at)}
                        </span>
                      </span>
                    </button>
                    <button
                      type="button"
                      aria-label="Dismiss notification"
                      disabled={deleteMutation.isPending}
                      onClick={(event) => {
                        event.stopPropagation()
                        deleteMutation.mutate(notification.api_identifier)
                      }}
                      className="absolute right-2 top-2 rounded p-1 text-muted-foreground/60 opacity-0 transition-opacity hover:bg-accent hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default NotificationBell
