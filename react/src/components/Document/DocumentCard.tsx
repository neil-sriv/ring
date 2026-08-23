import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Link } from "@tanstack/react-router"
import type { DocumentResponse } from "../../client"

export function DocumentCard(props: {
  document: DocumentResponse
}): JSX.Element {
  const createdDate = new Date(props.document.created_at)
  const updatedDate = props.document.updated_at
    ? new Date(props.document.updated_at)
    : null

  // Get content preview (first 100 characters)
  const getContentPreview = () => {
    if (!props.document.content) return "No content yet"
    const plainText = props.document.content.replace(/<[^>]*>/g, "") // Strip HTML tags
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
