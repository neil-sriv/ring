import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Bell, Loader2 } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  getUnreadCountNotificationsInboxUnreadCountGetOptions,
  getUnreadCountNotificationsInboxUnreadCountGetQueryKey,
  listInboxNotificationsInboxGetOptions,
  listInboxNotificationsInboxGetQueryKey,
  readAllInboxNotificationsInboxReadAllPostMutation,
  readInboxItemNotificationsInboxInboxApiIdReadPostMutation,
} from "../../client/@tanstack/react-query.gen"
import type { InboxItemResponse } from "../../client/types.gen"
import { inboxDestination } from "../../util/inboxHref"

const listOptions = listInboxNotificationsInboxGetOptions({
  query: { limit: 20 },
})
const countOptions = getUnreadCountNotificationsInboxUnreadCountGetOptions()

function formatInboxTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

export function InboxBell() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const { data: unread } = useQuery({
    ...countOptions,
    refetchInterval: 60_000,
  })
  const { data: items, isLoading } = useQuery({
    ...listOptions,
    enabled: open,
  })
  const unreadCount = unread?.unread_count ?? 0

  function refreshInbox() {
    void queryClient.invalidateQueries({
      queryKey: listInboxNotificationsInboxGetQueryKey({
        query: { limit: 20 },
      }),
    })
    void queryClient.invalidateQueries({
      queryKey: getUnreadCountNotificationsInboxUnreadCountGetQueryKey(),
    })
  }

  const markRead = useMutation({
    ...readInboxItemNotificationsInboxInboxApiIdReadPostMutation(),
    onSuccess: refreshInbox,
  })
  const markAll = useMutation({
    ...readAllInboxNotificationsInboxReadAllPostMutation(),
    onSuccess: refreshInbox,
  })

  async function openItem(item: InboxItemResponse) {
    if (item.unread) {
      await markRead.mutateAsync({
        path: { inbox_api_id: item.api_identifier },
      })
    }
    setOpen(false)
    await navigate(inboxDestination(item.href))
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={
            unreadCount > 0 ? `Inbox, ${unreadCount} unread` : "Inbox"
          }
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[0.625rem] font-medium text-primary-foreground">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0 sm:w-96">
        <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
          <p className="text-sm font-medium text-foreground">Inbox</p>
          {unreadCount > 0 && (
            <button
              type="button"
              className="text-xs font-medium text-primary hover:underline disabled:opacity-50"
              disabled={markAll.isPending}
              onClick={() => markAll.mutate({})}
            >
              Mark all read
            </button>
          )}
        </div>
        <div className="max-h-96 overflow-y-auto">
          {isLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          )}
          {!isLoading && (items?.length ?? 0) === 0 && (
            <p className="px-3 py-8 text-center text-sm text-muted-foreground">
              No notifications yet
            </p>
          )}
          {items?.map((item) => (
            <button
              key={item.api_identifier}
              type="button"
              className="flex w-full flex-col gap-0.5 border-b border-border px-3 py-2.5 text-left last:border-b-0 hover:bg-accent"
              onClick={() => {
                void openItem(item)
              }}
            >
              <span className="flex items-baseline justify-between gap-2">
                <span
                  className={
                    item.unread
                      ? "truncate text-sm font-medium text-foreground"
                      : "truncate text-sm text-muted-foreground"
                  }
                >
                  {item.title}
                </span>
                <span className="shrink-0 text-[0.6875rem] text-muted-foreground">
                  {formatInboxTime(item.created_at)}
                </span>
              </span>
              <span className="line-clamp-2 text-xs text-muted-foreground">
                {item.body}
              </span>
            </button>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
