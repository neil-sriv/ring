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
import { OpenAPI, PartiesService, UserLinked } from "./client";
import theme from "./theme";

OpenAPI.BASE = import.meta.env.VITE_API_URL + OpenAPI.BASE;
OpenAPI.TOKEN = async () => {
  return localStorage.getItem("access_token") || "";
};

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
  const resp = useQuery<UserLinked | null, Error>({
    queryKey: ["currentUser"],
    queryFn: PartiesService.readUserMePartiesMeGet,
    retry: false,
    refetchInterval: 5000,
    enabled: localStorage.getItem("access_token") !== null,
  });

  return resp.isLoading && !resp.isError && false ? null : (
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

if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/serviceWorker.js");
  });
}
