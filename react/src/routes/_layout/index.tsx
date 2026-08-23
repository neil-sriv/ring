import { Skeleton } from "@/components/ui/skeleton"
import { createFileRoute } from "@tanstack/react-router"

import { Suspense } from "react"
import { ErrorBoundary } from "react-error-boundary"
import { HomeDashboard } from "../../components/Home/HomeDashboard"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function HomeSkeleton() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <div className="border-b pb-6">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="mt-3 h-8 w-64" />
        <Skeleton className="mt-3 h-4 w-80 max-w-full" />
      </div>
      <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Skeleton className="h-44 w-full" />
        <Skeleton className="hidden h-44 w-full md:block" />
      </div>
      <Skeleton className="mt-10 h-36 w-full" />
    </div>
  )
}

function Dashboard() {
  return (
    <div className="w-full">
      <ErrorBoundary
        fallbackRender={({ error }) => (
          <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
            <div className="rounded-lg border border-dashed px-6 py-12 text-center text-sm text-muted-foreground">
              Something went wrong: {error.message}
            </div>
          </div>
        )}
      >
        <Suspense fallback={<HomeSkeleton />}>
          <HomeDashboard />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}
