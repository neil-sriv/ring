import { createFileRoute } from "@tanstack/react-router";
import MaintenanceMode from "../components/Common/MaintenanceMode";
import { isMaintenanceMode } from "../util/env";

export const Route = createFileRoute("/maintenance")({
  component: MaintenanceMode,
  beforeLoad: () => {
    // If maintenance mode is disabled, redirect to home
    if (!isMaintenanceMode()) {
      throw new Error("Maintenance mode is disabled");
    }
    return {};
  },
}); 