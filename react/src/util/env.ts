export function isMaintenanceMode() {
  const mode = import.meta.env.VITE_MAINTENANCE_MODE
  return mode === "true" || mode === true
}
