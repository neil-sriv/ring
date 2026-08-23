const DAY_MS = 86_400_000

function startOfLocalDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
}

/** Whole calendar days from `now` until `dateIso`, in local time. */
export function daysUntil(dateIso: string, now: Date = new Date()): number {
  return Math.round(
    (startOfLocalDay(new Date(dateIso)) - startOfLocalDay(now)) / DAY_MS,
  )
}

export function formatShortDate(
  dateIso: string,
  now: Date = new Date(),
): string {
  const date = new Date(dateIso)
  const isSameYear = date.getFullYear() === now.getFullYear()
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    ...(isSameYear ? {} : { year: "numeric" }),
  })
}

export interface DueInfo {
  label: string
  isUrgent: boolean
}

export function formatDueLabel(
  sendAtIso: string,
  now: Date = new Date(),
): DueInfo {
  const days = daysUntil(sendAtIso, now)
  if (days < 0) {
    // In-progress past its send date: held open until enough replies arrive.
    return { label: "Sending soon", isUrgent: true }
  }
  if (days === 0) {
    return { label: "Due today", isUrgent: true }
  }
  if (days === 1) {
    return { label: "Due tomorrow", isUrgent: true }
  }
  if (days <= 7) {
    return { label: `Due in ${days} days`, isUrgent: false }
  }
  return { label: `Due ${formatShortDate(sendAtIso, now)}`, isUrgent: false }
}

export function formatPublishedLabel(
  sendAtIso: string,
  now: Date = new Date(),
): string {
  const daysAgo = -daysUntil(sendAtIso, now)
  if (daysAgo <= 0) {
    return "Published today"
  }
  if (daysAgo === 1) {
    return "Published yesterday"
  }
  if (daysAgo <= 7) {
    return `Published ${daysAgo} days ago`
  }
  return `Published ${formatShortDate(sendAtIso, now)}`
}

export function formatDateChip(dateIso: string): {
  month: string
  day: string
} {
  const date = new Date(dateIso)
  return {
    month: date.toLocaleDateString(undefined, { month: "short" }),
    day: date.toLocaleDateString(undefined, { day: "numeric" }),
  }
}

export function formatWeekday(dateIso: string): string {
  return new Date(dateIso).toLocaleDateString(undefined, { weekday: "long" })
}
