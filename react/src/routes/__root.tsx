import { Outlet, createRootRouteWithContext, redirect } from "@tanstack/react-router";
import React, { Suspense } from "react";

import NotFound from "../components/Common/NotFound";
import { QueryClient } from "@tanstack/react-query";
import { AuthContext } from "../hooks/useAuth";
import { isMaintenanceMode } from "../util/env";

const loadDevtools = () =>
  Promise.all([
    import("@tanstack/router-devtools"),
    import("@tanstack/react-query-devtools"),
  ]).then(([routerDevtools, reactQueryDevtools]) => {
    return {
      default: () => (
        <>
          <routerDevtools.TanStackRouterDevtools />
          <reactQueryDevtools.ReactQueryDevtools />
        </>
      ),
    };
  });

const TanStackDevtools =
  process.env.NODE_ENV === "production" ? () => null : React.lazy(loadDevtools);

interface RouterContext {
  queryClient: QueryClient;
  auth: Partial<AuthContext>;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => (
    <>
      <Outlet />
      <Suspense>
        <TanStackDevtools />
      </Suspense>
    </>
  ),
  notFoundComponent: () => <NotFound />,
  beforeLoad: () => {
    // If maintenance mode is enabled and we're not already on the maintenance page,
    // redirect to maintenance
    if (isMaintenanceMode() && window.location.pathname !== "/maintenance") {
      throw redirect({
        to: "/maintenance",
      });
    }
    return {};
  },
});
