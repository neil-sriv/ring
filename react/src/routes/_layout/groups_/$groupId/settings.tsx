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
import { GroupLinked, PartiesService } from "../../../../client";
import GroupInformation from "../../../../components/Groups/GroupInformation";
import GroupMembershipSettings from "../../../../components/Groups/GroupMembershipSettings";
import GroupLoopSettings from "../../../../components/Groups/GroupLoopSettings";

export const Route = createFileRoute("/_layout/groups/$groupId/settings")({
  loader: async ({ context, params }): Promise<GroupLinked> => {
    const group = await context.queryClient.ensureQueryData({
      queryKey: ["group", params.groupId],
      queryFn: async () => {
        return await PartiesService.readGroupPartiesGroupGroupApiIdGet({
          groupApiId: params.groupId,
        });
      },
    });
    return group;
  },
  component: GroupSettings,
});

const tabsConfig = [
  { title: "Group Information", component: GroupInformation },
  { title: "Membership", component: GroupMembershipSettings },
  { title: "Loop Settings", component: GroupLoopSettings },
  // { title: "Danger zone", component: DeleteAccount },
];

function GroupSettings() {
  const finalTabs = false ? tabsConfig.slice(0, 3) : tabsConfig;
  const loadedGroup = Route.useLoaderData();

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
