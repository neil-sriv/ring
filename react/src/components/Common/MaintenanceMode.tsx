export default function MaintenanceMode() {
  return (
    <div className="mx-auto max-w-2xl py-20">
      <div className="flex flex-col items-center gap-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Maintenance Mode</h1>
        <p className="text-lg text-muted-foreground">
          We're currently performing scheduled maintenance to improve our
          infrastructure. Please check back later.
        </p>
      </div>
    </div>
  )
}
