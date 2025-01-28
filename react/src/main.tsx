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
import { readUserMePartiesMeGet } from "./client";
import theme from "./theme";

import { client } from "./client/client.gen";

client.setConfig({
  baseURL: import.meta.env.VITE_API_URL + "/api/v1",
  auth: async () => {
    return localStorage.getItem("access_token") || "";
  },
});

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
    queryKey: ["currentUser"],
    queryFn: () => {
      const resp = readUserMePartiesMeGet().then((resp) => resp.data);
      return resp;
    },
    retry: false,
    refetchInterval: 5000,
    enabled: localStorage.getItem("access_token") !== null,
  });

  return resp.isLoading && !resp.isError && resp.data && false ? null : (
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
