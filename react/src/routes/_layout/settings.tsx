import { createFileRoute } from "@tanstack/react-router"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Appearance from "../../components/UserSettings/Appearance"
import BuildInfo from "../../components/UserSettings/BuildInfo"
import ChangePassword from "../../components/UserSettings/ChangePassword"
import DeleteAccount from "../../components/UserSettings/DeleteAccount"
import UserInformation from "../../components/UserSettings/UserInformation"

const tabsConfig = [
  { title: "My profile", component: UserInformation, value: "profile" },
  { title: "Password", component: ChangePassword, value: "password" },
  { title: "Appearance", component: Appearance, value: "appearance" },
  { title: "Build", component: BuildInfo, value: "build" },
  { title: "Danger zone", component: DeleteAccount, value: "danger" },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
})

function UserSettings() {
  const finalTabs = tabsConfig

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
        Settings
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Your account, appearance, and preferences.
      </p>
      <Tabs defaultValue={finalTabs[0].value} className="mt-6">
        <TabsList>
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value} className="mt-6">
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
