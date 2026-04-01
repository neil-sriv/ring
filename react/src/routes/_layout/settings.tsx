import { createFileRoute } from "@tanstack/react-router"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Appearance from "../../components/UserSettings/Appearance"
import ChangePassword from "../../components/UserSettings/ChangePassword"
import DeleteAccount from "../../components/UserSettings/DeleteAccount"
import UserInformation from "../../components/UserSettings/UserInformation"

const tabsConfig = [
  { title: "My profile", component: UserInformation, value: "profile" },
  { title: "Password", component: ChangePassword, value: "password" },
  { title: "Appearance", component: Appearance, value: "appearance" },
  { title: "Danger zone", component: DeleteAccount, value: "danger" },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
})

function UserSettings() {
  const finalTabs = tabsConfig

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold text-center md:text-left py-12">
        User Settings
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
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
