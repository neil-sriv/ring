import { createFileRoute, redirect } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"

import { resolveShortLinkLinksShortLinkTokenGetOptions } from "../../../client/@tanstack/react-query.gen"

export const Route = createFileRoute("/_layout/s/$token")({
  // Sits under _layout so an unauthenticated visitor is sent to login with
  // `next` pointing back here, then lands on the target after signing in.
  loader: async ({ params, context }): Promise<void> => {
    const resolution = await context.queryClient.ensureQueryData({
      ...resolveShortLinkLinksShortLinkTokenGetOptions({
        path: { token: params.token },
      }),
    })
    throw redirect({
      to: "/loops/$loopId",
      params: { loopId: resolution.target_api_id },
      replace: true,
    })
  },
  component: ShortLinkRedirect,
  errorComponent: ShortLinkNotFound,
})

function ShortLinkRedirect() {
  return (
    <div className="flex w-full items-center justify-center pt-12">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  )
}

function ShortLinkNotFound() {
  return (
    <div className="flex w-full justify-center pt-12">
      <div className="max-w-md rounded-xl border border-border/50 bg-background/80 p-6 text-center shadow-md backdrop-blur-sm dark:border-border/30 dark:bg-background/60">
        <h2 className="text-xl font-bold text-foreground">Link not found</h2>
        <p className="pt-2 text-muted-foreground">
          This share link is invalid or has been revoked.
        </p>
      </div>
    </div>
  )
}
