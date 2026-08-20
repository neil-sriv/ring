import type { AxiosError } from "axios"
import {
  type PostSubscriptionNotificationsSubscriptionPostError,
  postSubscriptionNotificationsSubscriptionPost,
} from "../client"
import { formatApiErrorDetail } from "./misc"

export type SubscribeToPushResult =
  | { ok: true }
  | {
      ok: false
      reason:
        | "no_user"
        | "unsupported"
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
  // Avoid hanging forever on `.ready` when no SW is registered (common in
  // cloud/dev when SW_DEV/VITE_SW_DEV is false).
  return Promise.race([
    navigator.serviceWorker.ready,
    new Promise<null>((resolve) => {
      window.setTimeout(() => resolve(null), 800)
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
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    return {
      ok: false,
      reason: "unsupported",
      message: "Push notifications are not supported in this browser.",
    }
  }

  const registration = await getPushRegistration()
  if (!registration) {
    return {
      ok: false,
      reason: "no_service_worker",
      message:
        "Notifications need the app service worker. Try again after a full reload, or enable the PWA service worker in this environment.",
    }
  }

  const permission = await Notification.requestPermission()
  if (permission !== "granted") {
    return {
      ok: false,
      reason: "permission_denied",
      message:
        permission === "denied"
          ? "Notification permission was blocked. Allow notifications for this site in your browser settings."
          : "Notification permission is required to enable push alerts.",
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
