import { precacheAndRoute } from "workbox-precaching";
import { registerRoute } from "workbox-routing";
import { StaleWhileRevalidate } from "workbox-strategies";

// Precache static assets
precacheAndRoute(self.__WB_MANIFEST || []);

// Cache API requests
registerRoute(
  ({ request }) => request.url.startsWith("https://api.yourdomain.com/"),
  new StaleWhileRevalidate({
    cacheName: "api-cache",
  })
);

// Push notification event listener
self.addEventListener("push", (event) => {
  if (event.data) {
    const notificationData = event.data.json();
    console.log("Push event data:", notificationData);
    event.waitUntil(
      self.registration.showNotification(notificationData.title, {
        body: notificationData.body,
        icon: "/assets/images/pwa-192x192.png",
        badge: "/assets/images/pwa-192x192.png",
        data: notificationData.url,
      })
    );
  }
});

// Handle notification click
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  if (event.notification.data) {
    event.waitUntil(clients.openWindow(event.notification.data));
  }
});

// Handle onpushsubscriptionchange event
self.addEventListener("pushsubscriptionchange", function (event) {
  console.log("Push subscription expired. Resubscribing...");
});
