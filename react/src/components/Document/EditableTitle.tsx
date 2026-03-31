import {
  Box,
  Heading,
  Input,
  Spinner,
  useColorModeValue,
  useToast,
} from "@chakra-ui/react"
import { useEffect, useRef, useState } from "react"

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
  const toast = useToast()

  const textColor = useColorModeValue("gray.800", "white")
  const hoverBorderColor = useColorModeValue("blue.300", "blue.400")
  const focusBorderColor = useColorModeValue("blue.400", "blue.500")

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
      toast({
        title: "Title cannot be empty",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
      setEditValue(title) // Reset to original value
      setIsEditing(false)
      return
    }

    try {
      await onTitleChange(editValue.trim())
      setIsEditing(false)
    } catch (error) {
      console.error("Failed to update title:", error)
      toast({
        title: "Failed to update title",
        description: "Please try again",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
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

  if (isEditing) {
    return (
      <Input
        ref={inputRef}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleSaveEdit}
        size={size}
        fontSize={
          size === "lg" ? "1.5rem" : size === "xl" ? "1.875rem" : "1.25rem"
        }
        fontWeight="bold"
        textAlign={textAlign}
        color={color || textColor}
        border="2px solid"
        borderColor={focusBorderColor}
        borderRadius="md"
        px={3}
        py={2}
        bg="transparent"
        _focus={{
          borderColor: focusBorderColor,
          boxShadow: `0 0 0 1px ${focusBorderColor}`,
        }}
        isDisabled={isLoading}
      />
    )
  }

  return (
    <Box
      position="relative"
      w="full"
      cursor="pointer"
      _hover={{
        "&::after": {
          content: '""',
          position: "absolute",
          bottom: "-2px",
          left: 0,
          right: 0,
          height: "2px",
          bg: hoverBorderColor,
          borderRadius: "1px",
          opacity: 0.6,
        },
      }}
      onClick={handleStartEdit}
    >
      <Heading
        size={size}
        textAlign={textAlign}
        color={color || textColor}
        fontWeight="bold"
        lineHeight="shorter"
        wordBreak="break-word"
        _hover={{
          color: hoverBorderColor,
        }}
        transition="color 0.2s ease"
      >
        {title}
      </Heading>
      {isLoading && (
        <Box
          position="absolute"
          top="50%"
          right="-2rem"
          transform="translateY(-50%)"
        >
          <Spinner size="sm" color="blue.500" />
        </Box>
      )}
    </Box>
  )
}
