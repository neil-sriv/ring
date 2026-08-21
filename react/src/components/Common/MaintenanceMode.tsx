export default function MaintenanceMode() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-24">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="font-display text-3xl font-semibold tracking-tight md:text-4xl">
          We'll be right back
        </h1>
        <p className="max-w-md text-base text-muted-foreground">
          Ring is undergoing scheduled maintenance to improve our
          infrastructure. Please check back in a little while.
        </p>
      </div>
    </div>
  )
}
