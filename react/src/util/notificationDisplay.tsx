import {
  AlarmClock,
  Bell,
  Hourglass,
  Mail,
  MailOpen,
  MessageCircleQuestion,
  MessageSquareReply,
  UserPlus,
  Users,
} from "lucide-react"

import type { NotificationType } from "../client"

export interface NotificationTypeMeta {
  icon: React.ComponentType<{ className?: string }>
  /** Tailwind classes for the icon chip (text + background). */
  accentClassName: string
}

/** Per-event icon and accent for rendering a notification row. */
export function notificationTypeMeta(
  type: NotificationType,
): NotificationTypeMeta {
  switch (type) {
    case "letter_sent":
      return {
        icon: Mail,
        accentClassName: "text-primary bg-primary/10",
      }
    case "responses_open":
      return {
        icon: MailOpen,
        accentClassName: "text-emerald-600 bg-emerald-500/10",
      }
    case "letter_reminder":
      return {
        icon: AlarmClock,
        accentClassName: "text-amber-600 bg-amber-500/10",
      }
    case "awaiting_response":
      return {
        icon: Hourglass,
        accentClassName: "text-amber-600 bg-amber-500/10",
      }
    case "added_to_group":
      return {
        icon: UserPlus,
        accentClassName: "text-sky-600 bg-sky-500/10",
      }
    case "member_joined":
      return {
        icon: Users,
        accentClassName: "text-sky-600 bg-sky-500/10",
      }
    case "new_question":
      return {
        icon: MessageCircleQuestion,
        accentClassName: "text-violet-600 bg-violet-500/10",
      }
    case "new_response":
      return {
        icon: MessageSquareReply,
        accentClassName: "text-violet-600 bg-violet-500/10",
      }
    case "generic":
      return {
        icon: Bell,
        accentClassName: "text-muted-foreground bg-muted",
      }
    default: {
      const exhaustive: never = type
      throw new Error(`Unhandled notification type: ${exhaustive}`)
    }
  }
}
