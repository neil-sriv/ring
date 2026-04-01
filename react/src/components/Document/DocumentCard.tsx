import { Badge } from "@/components/ui/badge"
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
      <div className="h-full backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 p-6 rounded-xl shadow-md transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:border-primary relative">
        <Badge variant="secondary" className="text-xs absolute top-2 right-2">
          v{props.document.latest_snapshot_version}
        </Badge>

        <div className="flex flex-col items-start gap-3">
          <h3 className="text-lg font-semibold text-foreground">
            {props.document.name}
          </h3>

          <p className="text-sm text-muted-foreground line-clamp-3">
            {getContentPreview()}
          </p>

          <div className="flex flex-col items-start gap-1 w-full">
            <span className="text-xs text-muted-foreground">
              Created: {createdDate.toLocaleDateString()}
            </span>
            {updatedDate && (
              <span className="text-xs text-muted-foreground">
                Updated: {updatedDate.toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}
