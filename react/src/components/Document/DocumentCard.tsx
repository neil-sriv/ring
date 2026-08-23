import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Link } from "@tanstack/react-router"
import type { DocumentResponse } from "../../client"

// Elements whose boundaries should read as whitespace in the plain-text
// preview, so adjacent blocks don't run together ("JAPANdates" -> "JAPAN dates").
const BLOCK_BOUNDARY_SELECTOR =
  "p, h1, h2, h3, h4, h5, h6, li, blockquote, pre, br, hr, td, th"

function htmlToPreviewText(html: string): string {
  // DOMParser (vs. tag-stripping regex) also decodes entities like &amp;.
  const parsed = new DOMParser().parseFromString(html, "text/html")
  for (const element of parsed.body.querySelectorAll(BLOCK_BOUNDARY_SELECTOR)) {
    element.after(" ")
  }
  return (parsed.body.textContent ?? "").replace(/\s+/g, " ").trim()
}

export function DocumentCard(props: {
  document: DocumentResponse
}): JSX.Element {
  const createdDate = new Date(props.document.created_at)
  const updatedDate = props.document.updated_at
    ? new Date(props.document.updated_at)
    : null

  // Get content preview (first 50 characters)
  const getContentPreview = () => {
    if (!props.document.content) return "No content yet"
    const plainText = htmlToPreviewText(props.document.content)
    if (!plainText) return "No content yet"
    return plainText.length > 50
      ? `${plainText.substring(0, 50)}...`
      : plainText
  }

  return (
    <Link
      to="/documents/$documentId"
      params={{ documentId: props.document.api_identifier }}
      className="block h-full no-underline"
    >
      <Card className="flex h-full flex-col gap-2 p-5 transition-shadow hover:shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <h3 className="line-clamp-2 min-w-0 break-words font-display text-base font-medium">
            {props.document.name}
          </h3>
          <Badge variant="outline">
            v{props.document.latest_snapshot_version}
          </Badge>
        </div>

        <p className="text-sm text-muted-foreground line-clamp-3">
          {getContentPreview()}
        </p>

        <div className="mt-auto flex w-full flex-col items-start gap-0.5 pt-1">
          <span className="text-xs text-muted-foreground">
            Created: {createdDate.toLocaleDateString()}
          </span>
          {updatedDate && (
            <span className="text-xs text-muted-foreground">
              Updated: {updatedDate.toLocaleDateString()}
            </span>
          )}
        </div>
      </Card>
    </Link>
  )
}
