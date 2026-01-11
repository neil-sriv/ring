import {
  Box,
  Button,
  ButtonGroup,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
  Textarea,
  VStack,
  useToast,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { format } from "date-fns"
import { useState } from "react"
import { FiEdit2, FiMoreVertical, FiTrash2 } from "react-icons/fi"

import type { UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"
import {
  commentQueryKeys,
  deleteComment,
  updateComment,
} from "../../client/commentApi"
// Comment types will be added after API client generation

interface CommentItemProps {
  comment: any // Will be typed as CommentLinked after API client generation
  questionApiId: string
}

export default function CommentItem({
  comment,
  questionApiId,
}: CommentItemProps) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(comment.content)

  const isAuthor = currentUser?.api_identifier === comment.author.api_identifier
  const isAdmin = currentUser?.admin || false
  const canEdit = isAuthor && !comment.deleted_at
  const canDelete = isAdmin && !comment.deleted_at

  // Update comment mutation
  const updateMutation = useMutation({
    mutationFn: async (content: string) => {
      return await updateComment(comment.api_identifier, { content })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: commentQueryKeys.list(questionApiId),
      })
      setIsEditing(false)
      toast({
        title: "Comment updated",
        status: "success",
        duration: 3000,
      })
    },
    onError: (error: any) => {
      toast({
        title: "Failed to update comment",
        description: error.response?.data?.detail || "Something went wrong",
        status: "error",
        duration: 5000,
      })
    },
  })

  // Delete comment mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      return await deleteComment(comment.api_identifier)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: commentQueryKeys.list(questionApiId),
      })
      toast({
        title: "Comment deleted",
        status: "success",
        duration: 3000,
      })
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete comment",
        description: error.response?.data?.detail || "Something went wrong",
        status: "error",
        duration: 5000,
      })
    },
  })

  const handleUpdate = async () => {
    if (!editContent.trim() || editContent === comment.content) {
      setIsEditing(false)
      return
    }
    await updateMutation.mutateAsync(editContent)
  }

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this comment?")) {
      await deleteMutation.mutateAsync()
    }
  }

  return (
    <Box
      p={4}
      borderWidth="1px"
      borderRadius="md"
      borderColor={comment.deleted_at ? "red.200" : "gray.200"}
      bg={comment.deleted_at ? "red.50" : "white"}
      position="relative"
    >
      <VStack align="stretch" spacing={2}>
        <HStack justify="space-between" align="flex-start">
          <VStack align="flex-start" spacing={0}>
            <Text fontWeight="semibold">
              {comment.author.name || comment.author.email}
            </Text>
            <Text fontSize="sm" color="gray.500">
              {format(new Date(comment.created_at), "MMM d, yyyy 'at' h:mm a")}
              {comment.updated_at && " (edited)"}
              {comment.deleted_at && " (deleted)"}
            </Text>
          </VStack>

          {(canEdit || canDelete) && (
            <Menu>
              <MenuButton
                as={IconButton}
                icon={<FiMoreVertical />}
                variant="ghost"
                size="sm"
                aria-label="Comment options"
              />
              <MenuList>
                {canEdit && (
                  <MenuItem
                    icon={<FiEdit2 />}
                    onClick={() => setIsEditing(true)}
                  >
                    Edit
                  </MenuItem>
                )}
                {canDelete && (
                  <MenuItem
                    icon={<FiTrash2 />}
                    onClick={handleDelete}
                    color="red.500"
                  >
                    Delete
                  </MenuItem>
                )}
              </MenuList>
            </Menu>
          )}
        </HStack>

        {isEditing ? (
          <VStack align="stretch" spacing={2}>
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              resize="vertical"
              minH="80px"
            />
            <ButtonGroup size="sm">
              <Button
                colorScheme="blue"
                onClick={handleUpdate}
                isLoading={updateMutation.isPending}
              >
                Save
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setIsEditing(false)
                  setEditContent(comment.content)
                }}
              >
                Cancel
              </Button>
            </ButtonGroup>
          </VStack>
        ) : (
          <Text whiteSpace="pre-wrap">{comment.content}</Text>
        )}
      </VStack>
    </Box>
  )
}
