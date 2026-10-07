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

// Focus an already-open tab and go to the payload URL. Opening a new
// window is only the fallback when no same-origin client exists.
self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  const targetUrl = event.notification.data
  if (!targetUrl || typeof targetUrl !== "string") {
    return
  }
  event.waitUntil(
    (async () => {
      const target = new URL(targetUrl, self.location.origin)
      const windowClients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      })
      for (const client of windowClients) {
        if (new URL(client.url).origin !== target.origin) {
          continue
        }
        await client.focus()
        if ("navigate" in client) {
          try {
            await client.navigate(target.href)
            return
          } catch {
            // navigate can reject if the client is closing; open a window
          }
        }
        break
      }
      await self.clients.openWindow(target.href)
    })(),
  )
})

// Handle onpushsubscriptionchange event
self.addEventListener("pushsubscriptionchange", (event) => {
  console.log("Push subscription expired. Resubscribing...")
})
