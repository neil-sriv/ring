import {
  Box,
  Flex,
  Text,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
  useDisclosure,
  Textarea,
  Button,
  HStack,
} from "@chakra-ui/react";
import { HiDotsVertical } from "react-icons/hi";
import { FiEdit2, FiTrash2 } from "react-icons/fi";
import { useState } from "react";

interface CommentItemProps {
  comment: {
    api_identifier: string;
    content: string;
    created_at: string;
    updated_at?: string;
    author: {
      api_identifier: string;
      name: string;
      email: string;
    };
    is_deleted?: boolean;
  };
  currentUserId?: string;
  isAdmin?: boolean;
  onEdit: (commentId: string, newContent: string) => void;
  onDelete: (commentId: string) => void;
}

const CommentItem = ({
  comment,
  currentUserId,
  isAdmin,
  onEdit,
  onDelete,
}: CommentItemProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const subtextColor = useColorModeValue("ui.dim", "ui.dim");
  const bgColor = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const borderColor = useColorModeValue("ui.glass.light.border", "ui.glass.dark.border");

  const isAuthor = currentUserId === comment.author.api_identifier;
  const canEdit = isAuthor && !comment.is_deleted;
  const canDelete = isAdmin && !comment.is_deleted;

  const handleSaveEdit = () => {
    if (editContent.trim() && editContent !== comment.content) {
      onEdit(comment.api_identifier, editContent);
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditContent(comment.content);
    setIsEditing(false);
  };

  // Simple time ago formatting
  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} day${days !== 1 ? 's' : ''} ago`;
    
    // For older comments, show the date
    return date.toLocaleDateString();
  };

  const timeAgo = getTimeAgo(comment.created_at);

  return (
    <Box
      bg={bgColor}
      backdropFilter="blur(10px)"
      border="1px solid"
      borderColor={borderColor}
      p={4}
      borderRadius="lg"
      position="relative"
      opacity={comment.is_deleted ? 0.6 : 1}
    >
      <Flex justify="space-between" align="flex-start">
        <Box flex="1">
          <Flex align="center" mb={2}>
            <Text fontWeight="medium" color={textColor}>
              {comment.author.name}
            </Text>
            <Text fontSize="sm" color={subtextColor} ml={2}>
              {timeAgo}
            </Text>
            {comment.updated_at && !comment.is_deleted && (
              <Text fontSize="sm" color={subtextColor} ml={2}>
                (edited)
              </Text>
            )}
            {comment.is_deleted && (
              <Text fontSize="sm" color="red.500" ml={2}>
                (deleted)
              </Text>
            )}
          </Flex>

          {isEditing ? (
            <Box>
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                bg={bgColor}
                borderColor={borderColor}
                _hover={{
                  borderColor: "ui.primary",
                }}
                _focus={{
                  borderColor: "ui.primary",
                  boxShadow: "0 0 0 1px var(--chakra-colors-ui-primary)",
                }}
                minH="80px"
                mb={2}
              />
              <HStack spacing={2}>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleSaveEdit}
                  _hover={{
                    opacity: 0.9,
                    bg: "ui.primary",
                  }}
                  transition="all 0.2s ease-in-out"
                >
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="glass"
                  onClick={handleCancelEdit}
                >
                  Cancel
                </Button>
              </HStack>
            </Box>
          ) : (
            <Text color={textColor} whiteSpace="pre-wrap">
              {comment.is_deleted ? "[This comment has been deleted]" : comment.content}
            </Text>
          )}
        </Box>

        {(canEdit || canDelete) && !isEditing && (
          <Menu>
            <MenuButton
              as={IconButton}
              icon={<HiDotsVertical />}
              variant="ghost"
              size="sm"
              aria-label="Comment options"
              color={subtextColor}
              _hover={{
                bg: "ui.glass.light.background",
                _dark: {
                  bg: "ui.glass.dark.background",
                },
              }}
            />
            <MenuList
              bg={bgColor}
              backdropFilter="blur(10px)"
              borderColor={borderColor}
            >
              {canEdit && (
                <MenuItem
                  icon={<FiEdit2 />}
                  onClick={() => setIsEditing(true)}
                  _hover={{
                    bg: "ui.glass.light.background",
                    _dark: {
                      bg: "ui.glass.dark.background",
                    },
                  }}
                >
                  Edit
                </MenuItem>
              )}
              {canDelete && (
                <MenuItem
                  icon={<FiTrash2 />}
                  onClick={() => onDelete(comment.api_identifier)}
                  color="red.500"
                  _hover={{
                    bg: "red.50",
                    _dark: {
                      bg: "red.900",
                    },
                  }}
                >
                  Delete
                </MenuItem>
              )}
            </MenuList>
          </Menu>
        )}
      </Flex>
    </Box>
  );
};

export default CommentItem;