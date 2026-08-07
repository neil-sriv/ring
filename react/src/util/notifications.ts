import type { AxiosError } from "axios"
import {
  type PostSubscriptionNotificationsSubscriptionPostError,
  postSubscriptionNotificationsSubscriptionPost,
} from "../client"
import { formatApiErrorDetail } from "./misc"

const generateSubscription = async (): Promise<PushSubscription> => {
  const registration = await navigator.serviceWorker.ready
  const existingSubscription = await registration.pushManager.getSubscription()
  if (existingSubscription) {
    return existingSubscription
  }
  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY, // Ensure this is set in .env
  })
}

export async function subscribeToPush(user_api_id: string): Promise<void> {
  if (!user_api_id) {
    return
  }
  if (!("serviceWorker" in navigator)) {
    return
  }

  const permission = await Notification.requestPermission()

  if (permission !== "granted") {
    return
  }
  const subscription = await generateSubscription()

  const { endpoint, keys } = subscription.toJSON()

  if (!keys || !endpoint) {
    return
  }

  try {
    await postSubscriptionNotificationsSubscriptionPost({
      body: {
        endpoint,
        keys,
        user_api_identifier: user_api_id,
      },
      throwOnError: true,
    })
  } catch (err) {
    const axiosErr =
      err as AxiosError<PostSubscriptionNotificationsSubscriptionPostError>
    console.error(
      formatApiErrorDetail(
        axiosErr.response?.data?.detail,
        "Failed to register push subscription",
      ),
    )
  }
}
