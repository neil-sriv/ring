import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"
import ReactDOM from "react-dom/client"
import { Toaster } from "sonner"
import { routeTree } from "./routeTree.gen"

import { StrictMode } from "react"

import "./app.css"

import { registerSW } from "virtual:pwa-register"
import { readUserMePartiesMeGetOptions } from "./client/@tanstack/react-query.gen"
import { client } from "./client/client.gen"
import { initGlobalKeyboardShortcuts } from "./lib/globalKeyboardShortcuts"
import { isPublicAuthPath } from "./util/authRoutes"
import { httpsUpgradeUrl } from "./util/httpsUpgrade"

/* Dark mode initialization */
const savedTheme = localStorage.getItem("theme")
if (
  savedTheme === "dark" ||
  (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)
) {
  document.documentElement.classList.add("dark")
} else {
  document.documentElement.classList.remove("dark")
}
/**/

/* PWA: auto-reload when a new service worker is ready after deploy.
   Skip in DEV when SW_DEV=false (cloud HTTP Vite) — VitePWA already disables
   the dev SW, but calling registerSW still races and noisy-fails. */
if (!import.meta.env.DEV || import.meta.env.VITE_SW_DEV !== "false") {
  registerSW({ immediate: true })
}
/**/

/* vite Config */
const apiOrigin = import.meta.env.VITE_API_URL ?? ""

const httpsUrl = httpsUpgradeUrl(window.location, apiOrigin)
if (httpsUrl) {
  window.location.replace(httpsUrl)
}

client.setConfig({
  baseURL: apiOrigin ? `${apiOrigin}/api/v1` : "/api/v1",
  auth: async () => {
    return localStorage.getItem("access_token") || ""
  },
})
/**/

/* vite response interceptor */
client.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token")
      // Login, reset-password and register pages need the stale token cleared,
      // but navigating away would discard the one-time token in their URL.
      if (!isPublicAuthPath(window.location.pathname)) {
        const currentPath =
          window.location.pathname +
          window.location.search +
          window.location.hash
        const nextParam = encodeURIComponent(currentPath)
        window.location.href = `/login?next=${nextParam}`
      }
    }
    return Promise.reject(error)
  },
)
/**/

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: true,
    },
  },
})

const router = createRouter({
  routeTree,
  context: { queryClient, auth: undefined! },
})
initGlobalKeyboardShortcuts(router)
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

function App() {
  const resp = useQuery({
    ...readUserMePartiesMeGetOptions({}),
    retry: false,
    enabled: localStorage.getItem("access_token") !== null,
  })

  return (
    <RouterProvider
      router={router}
      context={{
        auth: {
          user: resp.data,
          isAuthenticated: !resp.isError && resp.data !== undefined,
        },
      }}
    />
  )
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster position="bottom-right" richColors closeButton />
    </QueryClientProvider>
  </StrictMode>,
)
