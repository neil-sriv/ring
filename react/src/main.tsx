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

/* PWA */
const updateSW = registerSW({
  onNeedRefresh() {
    if (confirm("New version available. Reload?")) {
      updateSW(true)
    }
  },
  onOfflineReady() {
    console.log("PWA is ready for offline use")
  },
})
/**/

/* vite Config */
client.setConfig({
  baseURL: `${import.meta.env.VITE_API_URL}/api/v1`,
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
      const currentPath =
        window.location.pathname + window.location.search + window.location.hash
      // Only add next parameter if we're not already on the login page
      if (window.location.pathname !== "/login") {
        const nextParam = encodeURIComponent(currentPath)
        window.location.href = `/login?next=${nextParam}`
      } else {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  },
)
/**/

const queryClient = new QueryClient()

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
    refetchInterval: 5000,
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
