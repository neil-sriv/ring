import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react"

export type MediaCarouselItem = {
  id: string
  render: () => ReactNode
}

type MediaCarouselProps = {
  items: MediaCarouselItem[]
  className?: string
}

export function MediaCarousel({ items, className }: MediaCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const itemRefs = useRef<(HTMLDivElement | null)[]>([])

  const clampIndex = useCallback(
    (index: number) => {
      if (items.length === 0) return 0
      if (index < 0) return 0
      if (index > items.length - 1) return items.length - 1
      return index
    },
    [items.length],
  )

  const scrollToIndex = useCallback(
    (index: number) => {
      const clamped = clampIndex(index)
      setActiveIndex(clamped)
      const target = itemRefs.current[clamped]
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          inline: "center",
          block: "nearest",
        })
      }
    },
    [clampIndex],
  )

  const handlePrevious = () => {
    scrollToIndex(activeIndex - 1)
  }

  const handleNext = () => {
    scrollToIndex(activeIndex + 1)
  }

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleScroll = () => {
      const children = itemRefs.current
      if (!children.length) return

      const containerRect = container.getBoundingClientRect()
      let closestIndex = activeIndex
      let closestDistance = Number.POSITIVE_INFINITY

      children.forEach((child, index) => {
        if (!child) return
        const rect = child.getBoundingClientRect()
        const childCenter = rect.left + rect.width / 2
        const containerCenter = containerRect.left + containerRect.width / 2
        const distance = Math.abs(childCenter - containerCenter)
        if (distance < closestDistance) {
          closestDistance = distance
          closestIndex = index
        }
      })

      setActiveIndex(closestIndex)
    }

    container.addEventListener("scroll", handleScroll, { passive: true })
    return () => {
      container.removeEventListener("scroll", handleScroll)
    }
  }, [activeIndex])

  if (!items.length) {
    return null
  }

  return (
    <div
      className={cn("relative w-full", "pt-2", className)}
      aria-label="Response media carousel"
    >
      <div
        ref={containerRef}
        className={cn(
          "flex w-full gap-3 overflow-x-auto pb-2",
          "snap-x snap-mandatory scroll-smooth",
          "no-scrollbar",
        )}
      >
        {items.map((item, index) => (
          <div
            key={item.id}
            ref={(el) => {
              itemRefs.current[index] = el
            }}
            className={cn("snap-center shrink-0", "w-auto")}
          >
            {item.render()}
          </div>
        ))}
      </div>

      {items.length > 1 && (
        <>
          <Button
            type="button"
            size="icon"
            variant="outline"
            className={cn(
              "absolute left-1 top-1/2 -translate-y-1/2",
            )}
            onClick={handlePrevious}
            aria-label="Previous media"
            disabled={activeIndex === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            size="icon"
            variant="outline"
            className={cn(
              "absolute right-1 top-1/2 -translate-y-1/2",
            )}
            onClick={handleNext}
            aria-label="Next media"
            disabled={activeIndex === items.length - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </>
      )}
    </div>
  )
}
