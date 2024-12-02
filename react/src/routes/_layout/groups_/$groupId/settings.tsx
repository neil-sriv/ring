import {
  Container,
  Heading,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { GroupLinked, PartiesService, UserLinked } from "../../../../client";
import GroupInformation from "../../../../components/Groups/GroupInformation";
import GroupMembershipSettings from "../../../../components/Groups/GroupMembershipSettings";
import GroupLoopSettings from "../../../../components/Groups/GroupLoopSettings";

export const Route = createFileRoute("/_layout/groups/$groupId/settings")({
  beforeLoad: async ({ context, params }): Promise<{ group?: GroupLinked }> => {
    const group = await context.queryClient.ensureQueryData({
      queryKey: ["group", params.groupId],
      queryFn: async () => {
        return await PartiesService.readGroupPartiesGroupGroupApiIdGet({
          groupApiId: params.groupId,
        });
      },
    });
    const currentUser = context.queryClient.getQueryData<UserLinked>([
      "currentUser",
    ]);
    if (currentUser?.api_identifier !== group.admin.api_identifier) {
      throw new Error("You are not authorized to view this page");
    }
    return { group: group };
  },
  loader: async ({ context: { group } }) => group,
  component: GroupSettings,
});

const tabsConfig = [
  { title: "Group Information", component: GroupInformation },
  { title: "Membership", component: GroupMembershipSettings },
  { title: "Loop Settings", component: GroupLoopSettings },
];

function GroupSettings() {
  const finalTabs = false ? tabsConfig.slice(0, 3) : tabsConfig;
  const loadedGroup = Route.useLoaderData();
  if (!loadedGroup) {
    return null;
  }

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        Group Settings
      </Heading>
      <Tabs variant="enclosed">
        <TabList>
          {finalTabs.map((tab, index) => (
            <Tab key={index}>{tab.title}</Tab>
          ))}
        </TabList>
        <TabPanels>
          {finalTabs.map((tab, index) => (
            <TabPanel key={index}>
              <tab.component groupId={loadedGroup.api_identifier} />
            </TabPanel>
          ))}
        </TabPanels>
      </Tabs>
    </Container>
  );
}
