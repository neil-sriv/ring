import { useEffect, useState } from "react"

/** Matches the `md` breakpoint where the sidebar becomes a static column. */
const MOBILE_MEDIA_QUERY = "(max-width: 767px)"
/** How far from the left edge a touch may start and still open the sidebar. */
const EDGE_ZONE_PX = 32
/** Travel needed before the drag is classified as horizontal or vertical. */
const AXIS_LOCK_PX = 10
/** Horizontal travel that commits the gesture. */
const COMMIT_DISTANCE_PX = 40

interface SidebarSwipeOptions {
  isOpen: boolean
  onOpen: () => void
  onClose: () => void
}

function isTextEntry(element: Element): boolean {
  return (
    element.closest(
      "input, textarea, select, [contenteditable=''], [contenteditable='true']",
    ) !== null
  )
}

function isHorizontallyScrollable(element: Element): boolean {
  if (element.scrollWidth <= element.clientWidth) {
    return false
  }
  const { overflowX } = window.getComputedStyle(element)
  return overflowX === "auto" || overflowX === "scroll"
}

/** Carousels, code blocks and wide tables own horizontal drags themselves. */
function hasHorizontalScrollAncestor(element: Element): boolean {
  let node: Element | null = element
  while (node) {
    if (isHorizontallyScrollable(node)) {
      return true
    }
    node = node.parentElement
  }
  return false
}

function isDialogOpen(): boolean {
  return (
    document.querySelector(
      '[role="dialog"][data-state="open"], [role="alertdialog"][data-state="open"]',
    ) !== null
  )
}

/**
 * Opens the mobile sidebar on a swipe in from the left edge and closes it on a
 * swipe back out. Desktop viewports keep the static sidebar, so the listeners
 * only run below `md`.
 */
export function useSidebarSwipe({
  isOpen,
  onOpen,
  onClose,
}: SidebarSwipeOptions): void {
  const [isMobile, setIsMobile] = useState(
    () => window.matchMedia(MOBILE_MEDIA_QUERY).matches,
  )

  useEffect(() => {
    const media = window.matchMedia(MOBILE_MEDIA_QUERY)
    const syncIsMobile = () => setIsMobile(media.matches)
    syncIsMobile()
    media.addEventListener("change", syncIsMobile)
    return () => media.removeEventListener("change", syncIsMobile)
  }, [])

  useEffect(() => {
    if (!isMobile) {
      return
    }

    let startX = 0
    let startY = 0
    let isTracking = false
    let isHorizontal = false

    const stopTracking = () => {
      isTracking = false
      isHorizontal = false
    }

    const handleTouchStart = (event: TouchEvent) => {
      stopTracking()
      if (event.touches.length !== 1) {
        return
      }
      const touch = event.touches[0]
      if (!isOpen && (touch.clientX > EDGE_ZONE_PX || isDialogOpen())) {
        return
      }
      const target = event.target
      if (
        target instanceof Element &&
        (isTextEntry(target) || hasHorizontalScrollAncestor(target))
      ) {
        return
      }
      startX = touch.clientX
      startY = touch.clientY
      isTracking = true
    }

    const handleTouchMove = (event: TouchEvent) => {
      if (!isTracking || event.touches.length !== 1) {
        return
      }
      const touch = event.touches[0]
      const deltaX = touch.clientX - startX
      const deltaY = touch.clientY - startY

      if (!isHorizontal) {
        if (
          Math.abs(deltaX) < AXIS_LOCK_PX &&
          Math.abs(deltaY) < AXIS_LOCK_PX
        ) {
          return
        }
        const isTowardsTarget = isOpen ? deltaX < 0 : deltaX > 0
        if (!isTowardsTarget || Math.abs(deltaX) <= Math.abs(deltaY)) {
          stopTracking()
          return
        }
        isHorizontal = true
      }

      // Claim the drag so the browser does not turn it into history navigation.
      if (event.cancelable) {
        event.preventDefault()
      }

      if (Math.abs(deltaX) < COMMIT_DISTANCE_PX) {
        return
      }
      stopTracking()
      if (isOpen) {
        onClose()
      } else {
        onOpen()
      }
    }

    window.addEventListener("touchstart", handleTouchStart, { passive: true })
    window.addEventListener("touchmove", handleTouchMove, { passive: false })
    window.addEventListener("touchend", stopTracking, { passive: true })
    window.addEventListener("touchcancel", stopTracking, { passive: true })
    return () => {
      window.removeEventListener("touchstart", handleTouchStart)
      window.removeEventListener("touchmove", handleTouchMove)
      window.removeEventListener("touchend", stopTracking)
      window.removeEventListener("touchcancel", stopTracking)
    }
  }, [isMobile, isOpen, onOpen, onClose])
}
