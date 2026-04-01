import { createFileRoute } from "@tanstack/react-router"

import { Suspense } from "react"
import { HomeDashboard } from "../../components/Home/HomeDashboard"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  return (
    <>
      <div className="w-full">
        <div className="pt-12 m-4">
          <Suspense fallback={<div>Loading...</div>}>
            <HomeDashboard />
          </Suspense>
        </div>
      </div>
    </>
  )
}
