import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from "@/components/ui/dialog"
import { ImagePlus, Loader2, X } from "lucide-react"
import { Dialog as DialogPrimitive } from "radix-ui"
import { useState } from "react"

/**
 * SingleUploadImage Component
 *
 * This component provides a user-friendly interface for uploading a single image.
 * It includes an option to preview the selected image and supports customization for size and rounding.
 *
 * @component
 *
 * @props {string} [size='100px'] - Specifies the dimensions of the upload area.
 * @props {string} [rounded='full'] - Defines the border-radius for the upload area, creating rounded corners.
 * @props {function} onUpdateFile (Required) - A callback function invoked when a new image is selected.
 *                                              It receives the selected image file as a parameter.
 *
 * @example
 * // Usage Example
 * <SingleUploadImage
 *   size="150px"
 *   rounded="md"
 *   onUpdateFile={handleFileUpdate}
 * />
 *
 * @example
 * // Import Example
 * import { SingleUploadImage } from './path-to-components';
 *
 * const YourComponent = () => {
 *   const handleFileUpdate = (file) => {
 *     // Handle the selected file (e.g., upload to server, update state)
 *     console.log('Selected File:', file);
 *   };
 *
 *   return (
 *     <SingleUploadImage
 *       size="150px"
 *       rounded="md"
 *       onUpdateFile={handleFileUpdate}
 *     />
 *   );
 * };
 */
type SingleUploadImageProps = {
  size?: string
  onUpdateFile(file: File): Promise<void>
  name: string
}

export function SingleUploadImage({
  size = "50px",
  onUpdateFile,
  name,
}: SingleUploadImageProps): JSX.Element {
  const [isUploading, setIsUploading] = useState(false)

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const { files } = event.target
    if (!files || files.length === 0) {
      return
    }
    setIsUploading(true)
    try {
      const uploadPromises = Array.from(files).map((file) => onUpdateFile(file))
      await Promise.all(uploadPromises)
    } finally {
      setIsUploading(false)
      event.target.value = ""
    }
  }

  return (
    <label
      htmlFor={name}
      className="flex items-center justify-center cursor-pointer overflow-hidden relative"
      style={{ width: size, height: size }}
    >
      <div className="absolute w-full h-full flex items-center justify-center hover:bg-black/40 transition-colors">
        <div className="flex flex-col items-center">
          {isUploading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ImagePlus className="h-4 w-4" />
          )}
        </div>
      </div>

      <input
        style={{ display: "none" }}
        type="file"
        id={name}
        name={name}
        multiple
        onChange={handleFileChange}
        disabled={isUploading}
        accept="image/*, video/*"
      />
    </label>
  )
}

interface S3MediaProps {
  s3Key: string
  alt?: string
  handleDelete?: () => void
  /** When set, opens a full-screen style viewer on click or tap. */
  expandable?: boolean
}

function S3MediaContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md hover:shadow-md transition-all duration-200 shadow-sm overflow-hidden block w-full max-w-[400px] min-w-0 p-2 relative">
      {children}
    </div>
  )
}

export function S3Image({
  s3Key,
  alt,
  handleDelete,
  expandable,
}: S3MediaProps) {
  const url = `https://du32exnxihxuf.cloudfront.net/${s3Key}`
  const [lightboxOpen, setLightboxOpen] = useState(false)

  const imageClassName =
    "max-w-[400px] max-h-[300px] object-contain hover:scale-[1.02] transition-all duration-200"

  const thumbnail = expandable ? (
    <button
      type="button"
      className="block p-0 m-0 border-0 bg-transparent cursor-zoom-in rounded-[inherit] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      onClick={() => setLightboxOpen(true)}
      aria-label="View image full screen"
    >
      <img
        src={url}
        alt={alt ?? ""}
        className={imageClassName}
        loading="lazy"
      />
    </button>
  ) : (
    <img src={url} alt={alt ?? ""} className={imageClassName} loading="lazy" />
  )

  return (
    <S3MediaContainer>
      {expandable ? (
        <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
          {thumbnail}
          <DialogPortal>
            <DialogOverlay className="bg-black/90" />
            <DialogPrimitive.Content
              className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
              aria-describedby={undefined}
            >
              <DialogTitle className="sr-only">
                {alt?.trim() ? alt : "Enlarged image"}
              </DialogTitle>
              <img
                src={url}
                alt={alt ?? ""}
                className="max-h-[calc(100dvh-2rem)] max-w-[calc(100vw-2rem)] w-auto object-contain"
              />
              <DialogClose className="absolute right-4 top-4 rounded-sm text-white drop-shadow-md opacity-70 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                <X className="h-6 w-6" />
                <span className="sr-only">Close</span>
              </DialogClose>
            </DialogPrimitive.Content>
          </DialogPortal>
        </Dialog>
      ) : (
        thumbnail
      )}
      {handleDelete && (
        <Button
          variant="destructive"
          size="icon"
          className="absolute top-3 right-3 opacity-70 hover:opacity-100 h-8 w-8"
          onClick={handleDelete}
          aria-label="Delete image"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </S3MediaContainer>
  )
}

export function S3Video({
  s3Key,
  handleDelete,
}: { s3Key: string; handleDelete?: () => void }) {
  const url = `https://du32exnxihxuf.cloudfront.net/${s3Key}`
  return (
    <S3MediaContainer>
      <video
        src={url}
        controls
        className="h-auto w-full max-h-[300px] object-contain"
      >
        <track kind="captions" />
      </video>
      {handleDelete && (
        <Button
          variant="destructive"
          size="icon"
          className="absolute top-3 right-3 opacity-70 hover:opacity-100 h-8 w-8"
          onClick={handleDelete}
          aria-label="Delete video"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </S3MediaContainer>
  )
}
