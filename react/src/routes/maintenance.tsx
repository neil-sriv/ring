import { createFileRoute, redirect } from "@tanstack/react-router"
import MaintenanceMode from "../components/Common/MaintenanceMode"
import { isMaintenanceMode } from "../util/env"

export const Route = createFileRoute("/maintenance")({
  component: MaintenanceMode,
  beforeLoad: () => {
    // Maintenance is off in normal deploys; deep links used to throw a
    // raw Error. Send visitors home instead.
    if (!isMaintenanceMode()) {
      throw redirect({ to: "/" })
    }
    return {}
  },
})
