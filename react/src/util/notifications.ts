import type { AxiosError } from "axios"
import {
  type PostSubscriptionNotificationsSubscriptionPostError,
  postSubscriptionNotificationsSubscriptionPost,
} from "../client"
import { formatApiErrorDetail } from "./misc"
import { pushOfferCopy, pushOfferKind, readPushClientFacts } from "./pushOffer"

export type SubscribeToPushResult =
  | { ok: true }
  | {
      ok: false
      reason:
        | "no_user"
        | "unsupported"
        | "ios_home_screen"
        | "no_service_worker"
        | "permission_denied"
        | "missing_subscription"
        | "api_error"
      message: string
    }

async function getPushRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (!("serviceWorker" in navigator)) {
    return null
  }
  const existing = await navigator.serviceWorker.getRegistration()
  if (existing) {
    return existing
  }
  // `.ready` never resolves when the dev server has the service worker
  // disabled. Cap the wait so an explicit enable click can report that.
  return Promise.race([
    navigator.serviceWorker.ready,
    new Promise<null>((resolve) => {
      window.setTimeout(() => resolve(null), 4000)
    }),
  ])
}

const generateSubscription = async (
  registration: ServiceWorkerRegistration,
): Promise<PushSubscription> => {
  const existingSubscription = await registration.pushManager.getSubscription()
  if (existingSubscription) {
    return existingSubscription
  }
  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY,
  })
}

export async function subscribeToPush(
  user_api_id: string,
): Promise<SubscribeToPushResult> {
  if (!user_api_id) {
    return {
      ok: false,
      reason: "no_user",
      message: "You must be signed in to enable notifications.",
    }
  }
  const offer = pushOfferKind(readPushClientFacts())
  if (offer === "ios_home_screen") {
    return {
      ok: false,
      reason: "ios_home_screen",
      message: pushOfferCopy(offer),
    }
  }
  if (offer === "unsupported") {
    return {
      ok: false,
      reason: "unsupported",
      message: pushOfferCopy(offer),
    }
  }
  if (offer === "denied") {
    return {
      ok: false,
      reason: "permission_denied",
      message: pushOfferCopy(offer),
    }
  }

  // requestPermission has to run before any await so the click's user
  // activation is still valid. Already-granted permission resolves immediately.
  const permission = await Notification.requestPermission()
  if (permission !== "granted") {
    return {
      ok: false,
      reason: "permission_denied",
      message:
        permission === "denied"
          ? pushOfferCopy("denied")
          : "Notification permission is required to enable push alerts.",
    }
  }

  const registration = await getPushRegistration()
  if (!registration) {
    return {
      ok: false,
      reason: "no_service_worker",
      message:
        "Notifications need this site's service worker. Reload the page and try again.",
    }
  }

  try {
    const subscription = await generateSubscription(registration)
    const { endpoint, keys } = subscription.toJSON()
    if (!keys || !endpoint) {
      return {
        ok: false,
        reason: "missing_subscription",
        message: "Could not read the browser push subscription.",
      }
    }

    await postSubscriptionNotificationsSubscriptionPost({
      body: {
        endpoint,
        keys,
        user_api_identifier: user_api_id,
      },
      throwOnError: true,
    })
    return { ok: true }
  } catch (err) {
    const axiosErr =
      err as AxiosError<PostSubscriptionNotificationsSubscriptionPostError>
    const message = formatApiErrorDetail(
      axiosErr.response?.data?.detail,
      err instanceof Error
        ? err.message
        : "Failed to register push subscription",
    )
    console.error(message)
    return { ok: false, reason: "api_error", message }
  }
}
