import { Flex, Spinner } from "@chakra-ui/react";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";

import Sidebar from "../components/Common/Sidebar";
import UserMenu from "../components/Common/UserMenu";
import {
  readUserMePartiesMeGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../client/@tanstack/react-query.gen";
import { subscribeToPush } from "../util/notifications";
import { useQueryClient } from "@tanstack/react-query";
import { UserLinked } from "../client/types.gen";

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async ({ context, location }): Promise<void> => {
    try {
      const user = await context.queryClient.ensureQueryData({
        ...readUserMePartiesMeGetOptions(),
      });
      context.auth.user = user;
    } catch (error) {
      // If authentication fails, redirect to login with the current path as next parameter
      // Only add next parameter if we're not already on the login page
      if (location.pathname !== "/login") {
        // Include hash fragment from window.location since TanStack Router's location might not have it
        const hash = typeof window !== "undefined" ? window.location.hash : "";
        const currentPath = location.pathname + location.search + hash;
        throw redirect({
          to: "/login",
          search: {
            next: currentPath,
          },
        });
      } else {
        // Already on login page, just redirect without next parameter
        throw redirect({
          to: "/login",
        });
      }
    }
  },
});

function Layout() {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
  subscribeToPush(currentUser?.api_identifier!);
  const isLoading = false;

  return (
    <Flex maxW="large" h="auto" position="relative">
      <Sidebar />
      {isLoading ? (
        <Flex justify="center" align="center" height="100vh" width="full">
          <Spinner size="xl" color="ui.main" />
        </Flex>
      ) : (
        <Outlet />
      )}
      <UserMenu />
    </Flex>
  );
}
