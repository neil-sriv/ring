import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogClose,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight, X } from "lucide-react"
import { Dialog as DialogPrimitive } from "radix-ui"
import { useEffect, useRef, useState } from "react"
import type { PublicQuestion, ResponseWithParticipant } from "../../client"
import { URLMatch, splitText } from "../../util/URLParse"
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
        <a
          key={`${index}${responseApiId}`}
          href={text}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline hover:opacity-80"
        >
          {text}
        </a>,
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
              <div className="rounded-md shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden block w-full max-w-[400px] min-w-0 p-2 relative">
                <img
                  src={`https://du32exnxihxuf.cloudfront.net/${image.s3_url}`}
                  alt={response.participant.name}
                  className="w-full max-h-[300px] object-contain hover:scale-[1.02] transition-all duration-200"
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

  useEffect(() => {
    if (activeLightboxIndex != null && dialogContentRef.current) {
      dialogContentRef.current.focus()
    }
  }, [activeLightboxIndex])

  return (
    <div
      className={cn(
        "my-2.5",
        isLateAnswer
          ? "p-3 bg-purple-50 border border-purple-200 rounded-md dark:bg-purple-900 dark:border-purple-600"
          : "",
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-lg font-semibold">{response.participant.name}</h3>
        {isLateAnswer && (
          <Badge
            variant="secondary"
            className="text-xs bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200"
          >
            Late Answer
          </Badge>
        )}
      </div>
      {/* <Text>{responseText}</Text> */}
      <TextBlockWithUrls
        texts={responseText}
        responseApiId={response.api_identifier}
      />
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
            >
              <DialogTitle className="sr-only">
                {activeLightboxIndex != null
                  ? `Photo from ${response.participant.name}`
                  : "Enlarged image"}
              </DialogTitle>
              {activeLightboxIndex != null && (
                <img
                  src={`https://du32exnxihxuf.cloudfront.net/${images[activeLightboxIndex].s3_url}`}
                  alt={response.participant.name}
                  className="max-h-[calc(100dvh-2rem)] max-w-[calc(100vw-2rem)] w-auto object-contain"
                />
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
    <div className="my-5">
      {question.author == null ? (
        <h2 className="text-2xl font-bold">{question.question_text}</h2>
      ) : (
        <h2 className="text-2xl font-bold">
          {question.author.name} asked: {question.question_text}
        </h2>
      )}
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
  )
}

export default PublishedQuestion
