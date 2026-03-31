import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { createFileRoute } from "@tanstack/react-router"
import type { GroupLinked } from "../../../../client"
import { readGroupPartiesGroupGroupApiIdGetOptions } from "../../../../client/@tanstack/react-query.gen"
import GroupInformation from "../../../../components/Groups/GroupInformation"
import GroupLoopSettings from "../../../../components/Groups/GroupLoopSettings"
import GroupMembershipSettings from "../../../../components/Groups/GroupMembershipSettings"

export const Route = createFileRoute("/_layout/groups/$groupId/settings")({
  beforeLoad: async ({ context, params }): Promise<{ group?: GroupLinked }> => {
    const group = await context.queryClient.ensureQueryData({
      ...readGroupPartiesGroupGroupApiIdGetOptions({
        path: { group_api_id: params.groupId },
      }),
    })
    const currentUser = context.auth.user
    if (currentUser?.api_identifier !== group.admin.api_identifier) {
      throw new Error("You are not authorized to view this page")
    }
    return { group: group }
  },
  loader: async ({ context: { group } }) => group,
  component: GroupSettings,
})

const tabsConfig = [
  {
    title: "Group Information",
    value: "group-information",
    component: GroupInformation,
  },
  {
    title: "Membership",
    value: "membership",
    component: GroupMembershipSettings,
  },
  {
    title: "Loop Settings",
    value: "loop-settings",
    component: GroupLoopSettings,
  },
]

function GroupSettings() {
  const finalTabs = false ? tabsConfig.slice(0, 3) : tabsConfig
  const loadedGroup = Route.useLoaderData()
  if (!loadedGroup) {
    return null
  }

  return (
    <div className="w-full">
      <h2 className="py-12 text-center text-2xl font-semibold md:text-left">
        Group Settings
      </h2>
      <Tabs defaultValue={finalTabs[0].value}>
        <TabsList>
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component groupId={loadedGroup.api_identifier} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
