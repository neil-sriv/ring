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

import { client } from "./client/client.gen";
import { readUserMePartiesMeGetOptions } from "./client/@tanstack/react-query.gen";
import { registerSW } from "virtual:pwa-register";

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
    return localStorage.getItem("access_token") || "";
  },
});
/**/

/* vite response interceptor */
client.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
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
    enabled: localStorage.getItem("access_token") !== null,
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
