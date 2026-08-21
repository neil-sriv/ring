import { useQuery } from "@tanstack/react-query"

import { Badge } from "@/components/ui/badge"
import { readVersionOptions } from "../../client/@tanstack/react-query.gen"
import {
  GITHUB_COMMIT_URL,
  fetchBuildVersion,
  formatAge,
  shortImageSha,
} from "../../util/buildVersion"

interface DeployRowProps {
  label: string
  sha: string | null | undefined
  branch: string | null | undefined
  timestampLabel: string
  timestamp: string | null | undefined
  imageSha?: string | null
  note?: string | null
  error?: string | null
}

function DeployRow({
  label,
  sha,
  branch,
  timestampLabel,
  timestamp,
  imageSha,
  note,
  error,
}: DeployRowProps) {
  const age = formatAge(timestamp)

  return (
    <div className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex flex-wrap items-center gap-2">
        {sha ? (
          <a
            href={`${GITHUB_COMMIT_URL}/${sha}`}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-xs text-primary underline underline-offset-2"
          >
            {sha.slice(0, 7)}
          </a>
        ) : (
          <span className="font-mono text-xs text-foreground">
            {error ?? "unknown"}
          </span>
        )}
        {branch ? <Badge variant="secondary">{branch}</Badge> : null}
        {imageSha ? (
          <span
            className="font-mono text-xs text-muted-foreground"
            title={imageSha}
          >
            image {shortImageSha(imageSha)}
          </span>
        ) : null}
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
  // Prod runs the image filesystem with no .git, so image_build is the
  // only truthful source there; a bind-mounted dev container is the
  // other way round.
  const apiBuild = api.data?.image_build.sha
    ? api.data.image_build
    : api.data?.git
  // The registry digest pins the exact image prod pulled; a locally built
  // image has no RepoDigest, so fall back to the local image id.
  const apiContainer = api.data?.docker.containers?.find(
    (container) => container.service === "api" || container.name === "ring-api",
  )
  const apiImageSha = apiContainer?.image_digest ?? apiContainer?.image_id

  return (
    <div className="w-full">
      <h3 className="text-base font-semibold">Build</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Which commit each half of the app is running.
      </p>
      <div className="mt-5 rounded-lg border bg-card p-4">
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
            imageSha={apiImageSha}
            note={apiBuild?.subject}
            error={api.isPending ? "loading…" : api.error?.message ?? "unknown"}
          />
        </div>
      </div>
    </div>
  )
}

export default BuildInfo
