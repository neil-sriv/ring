import { Flex, Spinner } from "@chakra-ui/react";
import { Outlet, createFileRoute } from "@tanstack/react-router";

import Sidebar from "../components/Common/Sidebar";
import UserMenu from "../components/Common/UserMenu";
import { PartiesService } from "../client/services";

export const Route = createFileRoute("/_layout")({
  component: Layout,
  loader: async ({ context }): Promise<void> => {
    await context.queryClient.ensureQueryData({
      queryKey: ["currentUser"],
      queryFn: async () => {
        return await PartiesService.readUserMePartiesMeGet();
      },
    });
  },
});

function Layout() {
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
