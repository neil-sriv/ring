import { ChakraProvider } from "@chakra-ui/react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import ReactDOM from "react-dom/client";
import { routeTree } from "./routeTree.gen";

import { StrictMode } from "react";
import theme from "./theme";

import { registerSW } from "virtual:pwa-register";
import { readUserMePartiesMeGetOptions } from "./client/@tanstack/react-query.gen";
import { client } from "./client/client.gen";
import { refreshAccessToken, clearTokens, getAccessToken, hasAccessToken } from "./util/auth";

/* PWA */
const updateSW = registerSW({
  onNeedRefresh() {
    if (confirm("New version available. Reload?")) {
      updateSW(true);
    }
  },
  onOfflineReady() {
    console.log("PWA is ready for offline use");
  },
});
/**/

/* vite Config */
client.setConfig({
  baseURL: import.meta.env.VITE_API_URL + "/api/v1",
  auth: async () => {
    return getAccessToken();
  },
});
/**/

/* Token refresh state to prevent concurrent refresh attempts */
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}

function redirectToLogin() {
  clearTokens();
  const currentPath = window.location.pathname + window.location.search + window.location.hash;
  // Only add next parameter if we're not already on the login page
  if (window.location.pathname !== "/login") {
    const nextParam = encodeURIComponent(currentPath);
    window.location.href = `/login?next=${nextParam}`;
  } else {
    window.location.href = "/login";
  }
}

/* vite response interceptor */
client.instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If the error is 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't try to refresh for the refresh endpoint itself
      if (originalRequest.url?.includes("/login/refresh-token")) {
        redirectToLogin();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Wait for the ongoing refresh to complete
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(client.instance(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshAccessToken();
        if (newToken) {
          onTokenRefreshed(newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client.instance(originalRequest);
        } else {
          redirectToLogin();
          return Promise.reject(error);
        }
      } catch (refreshError) {
        redirectToLogin();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
/**/

const queryClient = new QueryClient();

const router = createRouter({
  routeTree,
  context: { queryClient, auth: undefined! },
});
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
  const resp = useQuery({
    ...readUserMePartiesMeGetOptions({}),
    retry: false,
    refetchInterval: 5000,
    enabled: hasAccessToken(),
  });

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
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ChakraProvider>
  </StrictMode>
);
