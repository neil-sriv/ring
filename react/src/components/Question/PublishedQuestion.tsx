import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogClose,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from "@/components/ui/dialog"
import { ChevronLeft, ChevronRight, X } from "lucide-react"
import { Dialog as DialogPrimitive } from "radix-ui"
import { useEffect, useRef, useState } from "react"
import type { PublicQuestion, ResponseWithParticipant } from "../../client"
import { URLMatch, splitText } from "../../util/URLParse"
import LinkPreviewCard from "../Common/LinkPreviewCard"
import { MediaCarousel } from "../Common/MediaCarousel"
import { S3Video } from "../Common/SingleUploadImage"

function TextBlockWithUrls({
  texts,
  responseApiId,
}: {
  texts: string[]
  responseApiId: string
}): JSX.Element {
  const elements = new Array<JSX.Element>()
  texts.forEach((text, index) => {
    if (URLMatch(text) != null) {
      elements.push(
        <span key={`${index}${responseApiId}`}>
          <a
            href={text}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline underline-offset-2 transition-colors hover:text-primary/80"
          >
            {text}
          </a>
          <LinkPreviewCard url={text} />
        </span>,
      )
    } else {
      elements.push(
        <p className="whitespace-pre-line" key={`${index}${responseApiId}`}>
          {text}
        </p>,
      )
    }
  })
  return <>{elements}</>
}

function ResponseBlock({
  response,
  isLateAnswer,
}: { response: ResponseWithParticipant; isLateAnswer?: boolean }) {
  const [activeLightboxIndex, setActiveLightboxIndex] = useState<number | null>(
    null,
  )
  const dialogContentRef = useRef<HTMLDivElement | null>(null)
  const touchStartXRef = useRef<number | null>(null)
  const touchEndXRef = useRef<number | null>(null)

  let responseText = [response.response_text]
  const urlMatches = URLMatch(response.response_text)
  if (urlMatches != null) {
    responseText = splitText(response.response_text)
  }

  const images =
    response.images?.filter((image) => image.media_type === "image") ?? []

  let imageIndexCounter = 0

  const mediaItems =
    response.images?.map((image) => {
      const id = image.s3_url
      if (image.media_type === "image") {
        return {
          id,
          render: () => (
            <button
              type="button"
              className="block cursor-zoom-in focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              onClick={() => setActiveLightboxIndex(imageIndexCounter++)}
              aria-label={`View image from ${response.participant.name} full screen`}
            >
              <div className="block w-full max-w-[400px] min-w-0 overflow-hidden rounded-lg border bg-card">
                <img
                  src={`https://du32exnxihxuf.cloudfront.net/${image.s3_url}`}
                  alt={response.participant.name}
                  className="block w-full max-h-[300px] object-contain"
                  loading="lazy"
                />
              </div>
            </button>
          ),
        }
      }
      return {
        id,
        render: () => <S3Video s3Key={image.s3_url} />,
      }
    }) ?? []

  const showPreviousImage = () => {
    if (!images.length) return
    setActiveLightboxIndex((prev) => {
      if (prev == null) return prev
      if (prev <= 0) return 0
      return prev - 1
    })
  }

  const showNextImage = () => {
    if (!images.length) return
    setActiveLightboxIndex((prev) => {
      if (prev == null) return prev
      if (prev >= images.length - 1) return images.length - 1
      return prev + 1
    })
  }

  const handleLightboxKeyDown = (
    event: React.KeyboardEvent<HTMLDivElement>,
  ) => {
    if (!images.length) return
    if (event.key === "ArrowLeft") {
      event.preventDefault()
      showPreviousImage()
    } else if (event.key === "ArrowRight") {
      event.preventDefault()
      showNextImage()
    }
  }

  const handleTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    if (event.touches.length !== 1) return
    touchStartXRef.current = event.touches[0].clientX
    touchEndXRef.current = null
  }

  const handleTouchMove = (event: React.TouchEvent<HTMLDivElement>) => {
    if (event.touches.length !== 1) return
    touchEndXRef.current = event.touches[0].clientX
  }

  const handleTouchEnd = () => {
    if (touchStartXRef.current == null || touchEndXRef.current == null) return

    const deltaX = touchEndXRef.current - touchStartXRef.current
    const threshold = 40

    if (Math.abs(deltaX) < threshold) return

    if (deltaX < 0) {
      // swipe left -> next image
      showNextImage()
    } else {
      // swipe right -> previous image
      showPreviousImage()
    }

    touchStartXRef.current = null
    touchEndXRef.current = null
  }

  useEffect(() => {
    if (activeLightboxIndex != null && dialogContentRef.current) {
      dialogContentRef.current.focus()
    }
  }, [activeLightboxIndex])

  return (
    <div>
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <h3 className="text-sm font-medium">{response.participant.name}</h3>
        <span className="text-xs text-muted-foreground">
          {new Date(response.created_at).toLocaleDateString()}
        </span>
        {isLateAnswer && <Badge variant="info">Late Answer</Badge>}
      </div>
      {/* <Text>{responseText}</Text> */}
      <div className="mt-1.5 space-y-2 text-sm leading-relaxed text-foreground">
        <TextBlockWithUrls
          texts={responseText}
          responseApiId={response.api_identifier}
        />
      </div>
      {mediaItems.length > 0 && (
        <div className="mt-3">
          <MediaCarousel items={mediaItems} />
        </div>
      )}
      {images.length > 0 && (
        <Dialog
          open={activeLightboxIndex != null}
          onOpenChange={(open) => {
            if (!open) {
              setActiveLightboxIndex(null)
            }
          }}
        >
          <DialogPortal>
            <DialogOverlay className="bg-black/90" />
            <DialogPrimitive.Content
              ref={dialogContentRef}
              tabIndex={-1}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
              aria-describedby={undefined}
              onKeyDown={handleLightboxKeyDown}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
              onClick={(event) => {
                if (event.target === event.currentTarget) {
                  setActiveLightboxIndex(null)
                }
              }}
            >
              <DialogTitle className="sr-only">
                {activeLightboxIndex != null
                  ? `Photo from ${response.participant.name}`
                  : "Enlarged image"}
              </DialogTitle>
              {activeLightboxIndex != null && (
                <div
                  key={images[activeLightboxIndex].s3_url}
                  className="max-h-[calc(100dvh-2rem)] max-w-[calc(100vw-2rem)] w-auto animate-in fade-in-0 zoom-in-95 duration-200"
                >
                  <img
                    src={`https://du32exnxihxuf.cloudfront.net/${images[activeLightboxIndex].s3_url}`}
                    alt={response.participant.name}
                    className="max-h-[calc(100dvh-2rem)] max-w-[calc(100vw-2rem)] w-auto object-contain"
                  />
                </div>
              )}
              {images.length > 1 && (
                <>
                  <button
                    type="button"
                    onClick={showPreviousImage}
                    disabled={activeLightboxIndex === 0}
                    className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-black/60 p-2 text-white hover:bg-black/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-40 disabled:hover:bg-black/60"
                    aria-label="Previous image"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    onClick={showNextImage}
                    disabled={activeLightboxIndex === images.length - 1}
                    className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-black/60 p-2 text-white hover:bg-black/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-40 disabled:hover:bg-black/60"
                    aria-label="Next image"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </>
              )}
              <DialogClose className="absolute right-4 top-4 rounded-sm text-white drop-shadow-md opacity-70 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                <X className="h-6 w-6" />
                <span className="sr-only">Close</span>
              </DialogClose>
            </DialogPrimitive.Content>
          </DialogPortal>
        </Dialog>
      )}
    </div>
  )
}

function PublishedQuestion({
  question,
  letterSendAt,
}: {
  question: PublicQuestion
  letterSendAt?: string
}): JSX.Element {
  // Determine which responses are late answers
  // A response is considered "late" if it was submitted after the letter was scheduled to be sent
  const letterSendDate = letterSendAt ? new Date(letterSendAt) : null

  return (
    <div className="border-b py-6 last:border-b-0">
      <div className="space-y-1">
        {question.author != null && (
          <p className="text-xs text-muted-foreground">
            {question.author.name} asked:
          </p>
        )}
        <h2 className="font-display text-lg font-medium leading-relaxed">
          {question.question_text}
        </h2>
      </div>
      <div className="mt-5 space-y-5">
        {question.responses.map((response) => {
          const responseCreatedAt = new Date(response.created_at)
          const isLateAnswer = letterSendDate
            ? responseCreatedAt > letterSendDate
            : false

          return (
            <ResponseBlock
              response={response}
              key={response.api_identifier}
              isLateAnswer={isLateAnswer}
            />
          )
        })}
      </div>
    </div>
  )
}

export default PublishedQuestion
