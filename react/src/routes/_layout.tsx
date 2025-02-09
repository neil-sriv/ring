import { Flex, Spinner } from "@chakra-ui/react";
import { Outlet, createFileRoute } from "@tanstack/react-router";

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
  beforeLoad: async ({ context }): Promise<void> => {
    const user = await context.queryClient.ensureQueryData({
      ...readUserMePartiesMeGetOptions(),
    });
    context.auth.user = user;
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
