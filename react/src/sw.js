import { cleanupOutdatedCaches, precacheAndRoute } from "workbox-precaching"

precacheAndRoute(self.__WB_MANIFEST || [])
cleanupOutdatedCaches()

// Activate a freshly deployed worker immediately and take over open pages
self.addEventListener("install", () => {
  self.skipWaiting()
})
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

// Push notification event listener
self.addEventListener("push", (event) => {
  if (event.data) {
    const notificationData = event.data.json()
    console.log("Push event data:", notificationData)
    event.waitUntil(
      self.registration.showNotification(notificationData.title, {
        body: notificationData.body,
        icon: "/assets/images/pwa-192x192.png",
        badge: "/assets/images/pwa-192x192.png",
        data: notificationData.url,
      }),
    )
  }
})

// Handle notification click
self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  if (event.notification.data) {
    event.waitUntil(clients.openWindow("ring"))
  }
})

// Handle onpushsubscriptionchange event
self.addEventListener("pushsubscriptionchange", (event) => {
  console.log("Push subscription expired. Resubscribing...")
})
