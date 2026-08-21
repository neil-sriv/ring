/** Normalize FastAPI `detail` (string or validation error list) for UI display. */
export function formatApiErrorDetail(
  detail: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (typeof detail === "string" && detail.length > 0) {
    return detail
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first === "string" && first.length > 0) {
      return first
    }
    if (
      first &&
      typeof first === "object" &&
      "msg" in first &&
      typeof (first as { msg: unknown }).msg === "string"
    ) {
      return (first as { msg: string }).msg
    }
  }
  return fallback
}

export const emailPattern = {
  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  message: "Invalid email address",
}

export const namePattern = {
  value: /^[A-Za-z\s\u00C0-\u017F]{1,30}$/,
  message: "Invalid name",
}

export const passwordRules = (isRequired = true) => {
  const rules: any = {
    minLength: {
      value: 8,
      message: "Password must be at least 8 characters",
    },
  }

  if (isRequired) {
    rules.required = "Password is required"
  }

  return rules
}

export const confirmPasswordRules = (
  getValues: () => any,
  isRequired = true,
) => {
  const rules: any = {
    validate: (value: string) => {
      const password = getValues().password || getValues().new_password
      return value === password ? true : "The passwords do not match"
    },
  }

  if (isRequired) {
    rules.required = "Password confirmation is required"
  }

  return rules
}

/** Initials for avatar fallbacks: "Ada Lovelace" -> "AL", else first letter of email. */
export function userInitials(
  name?: string | null,
  email?: string | null,
): string {
  const trimmed = name?.trim()
  if (trimmed) {
    const parts = trimmed.split(/\s+/)
    const first = parts[0]?.[0] ?? ""
    const last = parts.length > 1 ? parts[parts.length - 1][0] : ""
    return (first + last).toUpperCase()
  }
  return email?.[0]?.toUpperCase() ?? "?"
}

export function toISOLocal(d: Date): string {
  const z = (n: number) => `0${n}`.slice(-2)
  const zz = (n: number) => `00${n}`.slice(-3)
  let off = d.getTimezoneOffset()
  const sign = off > 0 ? "-" : "+"
  off = Math.abs(off)

  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}T${z(
    d.getHours(),
  )}:${z(d.getMinutes())}:${z(d.getSeconds())}.${zz(
    d.getMilliseconds(),
  )}${sign}${z((off / 60) | 0)}:${z(off % 60)}`
}

/** Local `datetime-local` default: N days ahead at the given local hour. */
export function defaultLocalDateTimeValue(
  daysFromNow: number,
  hour = 21,
): string {
  const d = new Date()
  d.setDate(d.getDate() + daysFromNow)
  d.setHours(hour, 0, 0, 0)
  return toISOLocal(d).slice(0, 16)
}
