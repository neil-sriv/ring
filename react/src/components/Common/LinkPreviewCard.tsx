import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import type { LinkPreview } from "../../client"
import { unfurlLinkLinksUnfurlPostOptions } from "../../client/@tanstack/react-query.gen"

const HTTP_URL = /^https?:\/\//i

function hasRenderableContent(preview: LinkPreview): boolean {
  return Boolean(preview.title || preview.description || preview.image_url)
}

/**
 * Render a rich preview ("unfurl") card for a URL.
 *
 * Fetches Open Graph-style metadata from the backend and renders a compact
 * card linking to the page. Renders nothing for non-http(s) URLs, while the
 * request is in flight, on error, or when the page exposes no usable
 * metadata, so it degrades gracefully to the plain inline link beside it.
 */
function LinkPreviewCard({ url }: { url: string }): JSX.Element | null {
  const [imageFailed, setImageFailed] = useState(false)
  const isHttpUrl = HTTP_URL.test(url)

  const { data: preview } = useQuery({
    ...unfurlLinkLinksUnfurlPostOptions({ body: { url } }),
    enabled: isHttpUrl,
    retry: false,
    // Previews are effectively static; avoid refetching for every reader.
    staleTime: 60 * 60 * 1000,
    gcTime: 60 * 60 * 1000,
  })

  if (!isHttpUrl || preview == null || !hasRenderableContent(preview)) {
    return null
  }

  const showImage = Boolean(preview.image_url) && !imageFailed

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="my-2 flex max-w-[480px] overflow-hidden rounded-lg border bg-card text-card-foreground transition-colors hover:bg-accent/50"
    >
      {showImage && (
        <img
          src={preview.image_url ?? undefined}
          alt=""
          className="h-auto w-32 flex-shrink-0 self-stretch object-cover"
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      )}
      <div className="flex min-w-0 flex-col justify-center gap-1 p-3">
        <div className="flex items-center gap-1.5">
          {preview.favicon_url && (
            <img
              src={preview.favicon_url}
              alt=""
              className="h-4 w-4 flex-shrink-0 rounded-sm"
              loading="lazy"
              onError={(e) => {
                e.currentTarget.style.display = "none"
              }}
            />
          )}
          <span className="truncate text-xs text-muted-foreground">
            {preview.site_name || url}
          </span>
        </div>
        {preview.title && (
          <span className="line-clamp-2 text-sm font-medium leading-snug">
            {preview.title}
          </span>
        )}
        {preview.description && (
          <span className="line-clamp-2 text-xs text-muted-foreground">
            {preview.description}
          </span>
        )}
      </div>
    </a>
  )
}

export default LinkPreviewCard
