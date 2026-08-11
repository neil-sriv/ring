import { useQuery } from "@tanstack/react-query"

import { Badge } from "@/components/ui/badge"
import { readVersionOptions } from "../../client/@tanstack/react-query.gen"
import {
  GITHUB_COMMIT_URL,
  fetchBuildVersion,
  formatAge,
} from "../../util/buildVersion"

interface DeployRowProps {
  label: string
  sha: string | null | undefined
  branch: string | null | undefined
  timestampLabel: string
  timestamp: string | null | undefined
  note?: string | null
  error?: string | null
}

function DeployRow({
  label,
  sha,
  branch,
  timestampLabel,
  timestamp,
  note,
  error,
}: DeployRowProps) {
  const age = formatAge(timestamp)

  return (
    <div className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-foreground">{label}</span>
        {sha ? (
          <a
            href={`${GITHUB_COMMIT_URL}/${sha}`}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-sm text-primary underline underline-offset-2"
          >
            {sha.slice(0, 7)}
          </a>
        ) : (
          <span className="text-sm text-muted-foreground">
            {error ?? "unknown"}
          </span>
        )}
        {branch ? <Badge variant="secondary">{branch}</Badge> : null}
      </div>
      {timestamp ? (
        <span className="text-xs text-muted-foreground">
          {timestampLabel} {age ?? timestamp}
          {age ? ` · ${timestamp}` : ""}
        </span>
      ) : null}
      {note ? (
        <span className="text-xs text-muted-foreground">{note}</span>
      ) : null}
    </div>
  )
}

/**
 * Show which commit each half of the app is running.
 *
 * The frontend redeploys itself on every push (Cloudflare Workers Builds)
 * while the API only moves on an explicit host rollout, so the two shas
 * routinely differ.
 */
const BuildInfo = () => {
  const frontend = useQuery({
    queryKey: ["buildVersion"],
    queryFn: fetchBuildVersion,
    retry: false,
    staleTime: 60_000,
  })
  const api = useQuery({ ...readVersionOptions(), retry: false })
  const apiBuild = api.data?.image_build

  return (
    <div className="w-full">
      <div className="flex flex-col gap-6">
        <h3 className="text-sm font-semibold text-foreground">Build</h3>
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="divide-y">
            <DeployRow
              label="Frontend"
              sha={frontend.data?.sha}
              branch={frontend.data?.branch}
              timestampLabel="Deployed"
              timestamp={frontend.data?.built_at}
              note={
                frontend.data?.build_uuid
                  ? `Cloudflare build ${frontend.data.build_uuid}`
                  : null
              }
              error={
                frontend.isPending
                  ? "loading…"
                  : frontend.error?.message ?? "unknown"
              }
            />
            <DeployRow
              label="API"
              sha={apiBuild?.sha}
              branch={apiBuild?.branch}
              timestampLabel="Committed"
              timestamp={apiBuild?.committed_at}
              note={apiBuild?.subject}
              error={
                api.isPending ? "loading…" : api.error?.message ?? "unknown"
              }
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default BuildInfo
