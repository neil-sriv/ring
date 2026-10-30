import { useRouterState } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { subscribeToPush } from "../../util/notifications"
import {
  type PushOfferKind,
  isPushOfferDismissed,
  pushOfferCopy,
  pushOfferDismissKey,
  pushOfferKind,
  readPushClientFacts,
} from "../../util/pushOffer"

const BANNER_KINDS = ["enable", "ios_home_screen"] as const

function readDismissedBannerKinds(): Set<PushOfferKind> {
  const dismissed = new Set<PushOfferKind>()
  for (const offer of BANNER_KINDS) {
    if (
      isPushOfferDismissed(offer, (key) => window.localStorage.getItem(key))
    ) {
      dismissed.add(offer)
    }
  }
  return dismissed
}

function usePushOffer() {
  const [kind, setKind] = useState<PushOfferKind>(() =>
    pushOfferKind(readPushClientFacts()),
  )
  return {
    kind,
    refresh: () => setKind(pushOfferKind(readPushClientFacts())),
  }
}

function EnablePushButton({
  userApiId,
  onComplete,
}: {
  userApiId: string
  onComplete: () => void
}) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // `pending` alone is not enough: same-tick double-clicks both pass
  // `if (pending)` before React re-renders with disabled={true}.
  const enableInFlightRef = useRef(false)

  async function onClick() {
    if (enableInFlightRef.current || pending) {
      return
    }
    enableInFlightRef.current = true
    setPending(true)
    setError(null)
    try {
      const result = await subscribeToPush(userApiId)
      if (result.ok) {
        toast.success("Notifications are on", {
          id: "enable-notifications",
          description:
            "This browser will get alerts when something new arrives.",
          duration: 8000,
        })
        onComplete()
        return
      }
      setError(result.message)
      toast.error("Couldn't enable notifications", {
        id: "enable-notifications",
        description: result.message,
        duration: 8000,
      })
    } finally {
      enableInFlightRef.current = false
      setPending(false)
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pending}
          onClick={() => {
            void onClick()
          }}
        >
          {pending && <Loader2 className="h-4 w-4 animate-spin" />}
          Enable notifications
        </Button>
      </div>
      {error && (
        <p
          role="status"
          aria-live="polite"
          className="max-w-md text-sm text-destructive"
        >
          Couldn't enable notifications: {error}
        </p>
      )}
    </div>
  )
}

export function PushOfferBanner({ userApiId }: { userApiId: string }) {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const { kind, refresh } = usePushOffer()
  const [dismissedKinds, setDismissedKinds] = useState(readDismissedBannerKinds)
  if (
    dismissedKinds.has(kind) ||
    pathname === "/settings" ||
    (kind !== "enable" && kind !== "ios_home_screen")
  ) {
    return null
  }

  function dismiss() {
    window.localStorage.setItem(pushOfferDismissKey(kind), "1")
    setDismissedKinds((current) => {
      const next = new Set(current)
      next.add(kind)
      return next
    })
  }

  return (
    <div className="border-b border-border bg-card px-4 py-3 pr-14 md:px-8 md:pr-20">
      <div className="flex max-w-3xl flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <p className="text-sm text-muted-foreground sm:pt-1.5">
          {pushOfferCopy(kind)}
        </p>
        <div className="flex shrink-0 items-start gap-2">
          {kind === "enable" && (
            <EnablePushButton userApiId={userApiId} onComplete={refresh} />
          )}
          <Button type="button" variant="ghost" size="sm" onClick={dismiss}>
            Not now
          </Button>
        </div>
      </div>
    </div>
  )
}

export function PushNotificationSettings({
  userApiId,
}: {
  userApiId: string | undefined
}) {
  const { kind, refresh } = usePushOffer()

  return (
    <section>
      <h3 className="text-base font-semibold">Notifications</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">
        {pushOfferCopy(kind)}
      </p>
      {kind === "enable" && userApiId && (
        <div className="mt-5">
          <EnablePushButton userApiId={userApiId} onComplete={refresh} />
        </div>
      )}
    </section>
  )
}
