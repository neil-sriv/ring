import { useCallback, useEffect, useRef } from "react"

export function useAutoResizeTextarea(value: string) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const minHeightRef = useRef<number | null>(null)

  const captureMinHeight = useCallback((node: HTMLTextAreaElement | null) => {
    if (node && minHeightRef.current === null) {
      minHeightRef.current = node.offsetHeight
    }
    ;(
      textareaRef as React.MutableRefObject<HTMLTextAreaElement | null>
    ).current = node
  }, [])

  useEffect(() => {
    void value
    const textarea = textareaRef.current
    if (!textarea) return

    textarea.style.height = "auto"
    const minH = minHeightRef.current ?? 0
    textarea.style.height = `${Math.max(textarea.scrollHeight, minH)}px`
  }, [value])

  return captureMinHeight
}
