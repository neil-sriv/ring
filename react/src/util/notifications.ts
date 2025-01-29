export const subscribeToPush = async (): Promise<void> => {
  if (!("serviceWorker" in navigator)) {
    console.error("Service Workers are not supported in this browser.");
    return;
  }

  const permission = await Notification.requestPermission();

  if (permission !== "granted") {
    console.warn("Push notifications permission denied.");
    return;
  }

  console.log(permission);
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: import.meta.env.VITE_VAPID_PUBLIC_KEY, // Ensure this is set in .env
  });

  console.log("Push subscription:", subscription);
  console.log(subscription.toJSON());
  console.log(subscription.getKey("p256dh"));
  console.log(subscription.getKey("auth"));

  function arrayBufferToString(buffer: ArrayBuffer): string {
    const decoder = new TextDecoder("utf-8"); // You can specify other encodings if necessary
    return decoder.decode(buffer);
  }
  console.log(arrayBufferToString(subscription.getKey("p256dh")!));
  console.log(arrayBufferToString(subscription.getKey("auth")!));

  //   // Send subscription to the server for push notifications
  //   await fetch("/api/subscribe", {
  //     method: "POST",
  //     body: JSON.stringify(subscription),
  //     headers: { "Content-Type": "application/json" },
  //   });
};
