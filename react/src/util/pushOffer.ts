export interface PushClientFacts {
  userAgent: string
  platform: string
  maxTouchPoints: number
  standaloneDisplay: boolean
  hasServiceWorker: boolean
  hasPushManager: boolean
  hasNotification: boolean
  permission: "default" | "granted" | "denied" | "unknown"
}

export type PushOfferKind =
  | "enable"
  | "enabled"
  | "denied"
  | "ios_home_screen"
  | "unsupported"

const IOS_DEVICE = /iPad|iPhone|iPod/

export function isIosWebKit(
  facts: Pick<PushClientFacts, "userAgent" | "platform" | "maxTouchPoints">,
): boolean {
  if (IOS_DEVICE.test(facts.userAgent)) {
    return true
  }
  // iPadOS reports a desktop Macintosh UA. Touch points keep a real Mac out.
  return facts.platform === "MacIntel" && facts.maxTouchPoints > 1
}

export function canSubscribeInTab(facts: PushClientFacts): boolean {
  return facts.hasServiceWorker && facts.hasPushManager && facts.hasNotification
}

// iOS Safari exposes PushManager only after Add to Home Screen. Every other
// browser that already has Notification + Push can subscribe from a tab.
export function pushOfferKind(facts: PushClientFacts): PushOfferKind {
  if (canSubscribeInTab(facts)) {
    if (facts.permission === "granted") {
      return "enabled"
    }
    if (facts.permission === "denied") {
      return "denied"
    }
    return "enable"
  }
  if (isIosWebKit(facts) && !facts.standaloneDisplay) {
    return "ios_home_screen"
  }
  return "unsupported"
}

export function pushOfferDismissKey(kind: PushOfferKind): string {
  return `ring.push-offer-dismissed.${kind}`
}

// Dismiss is per offer. iOS shares site storage with the Home Screen web
// app, so a "Not now" on the Add to Home Screen tip must not hide the
// later Enable button once Push is available.
export function isPushOfferDismissed(
  kind: PushOfferKind,
  getItem: (key: string) => string | null,
): boolean {
  return getItem(pushOfferDismissKey(kind)) === "1"
}

export function pushOfferCopy(kind: PushOfferKind): string {
  switch (kind) {
    case "enable":
      return "Get notifications in the web app when something new arrives."
    case "enabled":
      return "Notifications are on for this browser."
    case "denied":
      return "Notifications are blocked for this site. Allow them in your browser settings."
    case "ios_home_screen":
      return "Background alerts on iPhone and iPad need Add to Home Screen. While this tab is open, new items still show up in your inbox."
    case "unsupported":
      return "This browser can't receive background alerts. While this tab is open, new items still show up in your inbox."
  }
}

export function readPushClientFacts(): PushClientFacts {
  const nav = navigator as Navigator & { standalone?: boolean }
  const standaloneDisplay =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    nav.standalone === true
  const hasNotification = "Notification" in window
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    maxTouchPoints: navigator.maxTouchPoints ?? 0,
    standaloneDisplay,
    hasServiceWorker: "serviceWorker" in navigator,
    hasPushManager: "PushManager" in window,
    hasNotification,
    permission: hasNotification ? Notification.permission : "unknown",
  }
}
