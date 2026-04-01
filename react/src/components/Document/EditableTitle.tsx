import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import useCustomToast from "../../hooks/useCustomToast"

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
      console.error("Failed to update title:", error)
      showToast("Failed to update title", "Please try again", "error")
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
    sm: "text-xl",
    md: "text-2xl",
    lg: "text-3xl",
    xl: "text-4xl",
    "2xl": "text-5xl",
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
          "font-bold border-2 border-blue-400 dark:border-blue-500 bg-transparent px-3 py-2 h-auto focus-visible:ring-blue-400",
          color,
        )}
        disabled={isLoading}
      />
    )
  }

  return (
    <div
      className="relative w-full cursor-pointer group"
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
          "font-bold leading-tight break-words transition-colors duration-200 text-gray-800 dark:text-white group-hover:text-blue-400 dark:group-hover:text-blue-400",
          color,
        )}
      >
        {title}
      </h2>
      <div className="absolute bottom-[-2px] left-0 right-0 h-0.5 bg-blue-300 dark:bg-blue-400 rounded-sm opacity-0 group-hover:opacity-60 transition-opacity duration-200" />
      {isLoading && (
        <div className="absolute top-1/2 -right-8 -translate-y-1/2">
          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
        </div>
      )}
    </div>
  )
}
