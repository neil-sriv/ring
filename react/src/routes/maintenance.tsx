import { createFileRoute } from "@tanstack/react-router";
import MaintenanceMode from "../components/Common/MaintenanceMode";

export const Route = createFileRoute("/maintenance")({
  component: MaintenanceMode,
  beforeLoad: () => {
    // If maintenance mode is disabled, redirect to home
    if (!import.meta.env.VITE_MAINTENANCE_MODE) {
      throw new Error("Maintenance mode is disabled");
    }
    return {};
  },
}); 