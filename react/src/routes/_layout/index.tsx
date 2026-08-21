import { createFileRoute } from "@tanstack/react-router"

import { Suspense } from "react"
import { HomeDashboard } from "../../components/Home/HomeDashboard"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  return (
    <div className="w-full">
      <Suspense
        fallback={
          <div className="mx-auto w-full max-w-5xl px-4 py-8 text-sm text-muted-foreground md:px-8">
            Loading...
          </div>
        }
      >
        <HomeDashboard />
      </Suspense>
    </div>
  )
}
