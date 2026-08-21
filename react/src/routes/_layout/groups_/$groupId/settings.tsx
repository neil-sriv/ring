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
  const finalTabs = tabsConfig
  const loadedGroup = Route.useLoaderData()
  if (!loadedGroup) {
    return null
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
        Group Settings
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">{loadedGroup.name}</p>
      <div className="mt-6">
        <Tabs defaultValue={finalTabs[0].value}>
          <TabsList>
            {finalTabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.title}
              </TabsTrigger>
            ))}
          </TabsList>
          {finalTabs.map((tab) => (
            <TabsContent key={tab.value} value={tab.value} className="mt-6">
              <tab.component groupId={loadedGroup.api_identifier} />
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  )
}
