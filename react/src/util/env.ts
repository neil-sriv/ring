export function isMaintenanceMode() {
    console.log(import.meta.env);
    const mode = import.meta.env.VITE_MAINTENANCE_MODE;
    return mode === "true" || mode === true;
} 