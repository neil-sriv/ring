import {
  postSubscriptionNotificationsSubscriptionPost,
  PostSubscriptionNotificationsSubscriptionPostError,
} from "../client";
import { AxiosError } from "axios";

export async function subscribeToPush(user_api_id: string): Promise<void> {
  if (!("serviceWorker" in navigator)) {
    console.error("Service Workers are not supported in this browser.");
    return;
  }

  const permission = await Notification.requestPermission();

  if (permission !== "granted") {
    console.warn("Push notifications permission denied.");
    return;
  }

  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY, // Ensure this is set in .env
  });
  console.log(subscription.toJSON());

  const { endpoint, keys } = subscription.toJSON();

  if (!keys) {
    console.error("No keys found in the subscription object.");
    return;
  }
  if (!endpoint) {
    console.error("No endpoint found in the subscription object.");
    return;
  }

  //  Send subscription to the server for push notifications
  await postSubscriptionNotificationsSubscriptionPost({
    body: {
      endpoint,
      keys,
      user_api_identifier: user_api_id,
    },
  })
    .catch(
      (err: AxiosError<PostSubscriptionNotificationsSubscriptionPostError>) => {
        const errDetail =
          err.response?.data.detail ||
          "no error detail, please contact support";
        console.error(errDetail);
      }
    )
    .then((resp) => {
      console.log(resp);
    });
}
