import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

interface EditableTitleProps {
  title: string
  onTitleChange: (newTitle: string) => Promise<void>
  isLoading?: boolean
  size?: "sm" | "md" | "lg" | "xl" | "2xl"
  textAlign?: "left" | "center" | "right"
  color?: string
}

export function EditableTitle({
  title,
  onTitleChange,
  isLoading = false,
  size = "lg",
  textAlign = "left",
  color,
}: EditableTitleProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(title)
  const inputRef = useRef<HTMLInputElement>(null)
  const showToast = useCustomToast()

  // Update editValue when title prop changes
  useEffect(() => {
    setEditValue(title)
  }, [title])

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleStartEdit = () => {
    setIsEditing(true)
    setEditValue(title)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditValue(title)
  }

  const handleSaveEdit = async () => {
    if (editValue.trim() === title.trim()) {
      setIsEditing(false)
      return
    }

    if (!editValue.trim()) {
      showToast("Title cannot be empty", "", "error")
      setEditValue(title) // Reset to original value
      setIsEditing(false)
      return
    }

    try {
      await onTitleChange(editValue.trim())
      setIsEditing(false)
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: unknown }>
      showToast(
        "Failed to update title",
        formatApiErrorDetail(
          axiosError.response?.data?.detail,
          "Please try again",
        ),
        "error",
      )
      setEditValue(title) // Reset to original value
      setIsEditing(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSaveEdit()
    } else if (e.key === "Escape") {
      e.preventDefault()
      handleCancelEdit()
    }
  }

  const sizeClasses = {
    sm: "text-lg",
    md: "text-xl",
    lg: "text-2xl md:text-3xl",
    xl: "text-3xl",
    "2xl": "text-4xl",
  }

  const alignClasses = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
  }

  if (isEditing) {
    return (
      <Input
        ref={inputRef}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleSaveEdit}
        className={cn(
          sizeClasses[size],
          alignClasses[textAlign],
          "h-auto rounded-md border-transparent bg-transparent px-2 py-1 font-display font-semibold tracking-tight shadow-none",
          color,
        )}
        disabled={isLoading}
      />
    )
  }

  return (
    <div
      className="relative w-full cursor-pointer rounded-md transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/30"
      onClick={handleStartEdit}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          handleStartEdit()
        }
      }}
      role="button"
      tabIndex={0}
    >
      <h2
        className={cn(
          sizeClasses[size],
          alignClasses[textAlign],
          "break-words border border-transparent px-2 py-1 font-display font-semibold tracking-tight",
          color,
        )}
      >
        {title}
      </h2>
      {isLoading && (
        <div className="absolute top-1/2 -right-8 -translate-y-1/2">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
      )}
    </div>
  )
}
