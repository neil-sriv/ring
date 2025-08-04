import {
  Box,
  VStack,
  Heading,
  Textarea,
  Button,
  Text,
  Flex,
  Spinner,
  Center,
  useColorModeValue,
  Alert,
  AlertIcon,
  HStack,
} from "@chakra-ui/react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import CommentItem from "./CommentItem";
import useCustomToast from "../../hooks/useCustomToast";
import { UserLinked } from "../../client";
import { 
  createComment, 
  getComments, 
  updateComment, 
  deleteComment, 
  commentQueryKeys 
} from "../../client/commentApi";

interface Comment {
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
}

interface CommentSectionProps {
  questionApiId: string;
  currentUser?: UserLinked;
}

const CommentSection = ({ questionApiId, currentUser }: CommentSectionProps) => {
  const [newComment, setNewComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();
  const showToast = useCustomToast();
  
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const bgColor = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const borderColor = useColorModeValue("ui.glass.light.border", "ui.glass.dark.border");

  // Fetch comments query
  const { data: commentsData, isLoading, error } = useQuery({
    queryKey: commentQueryKeys.list(questionApiId),
    queryFn: () => getComments(questionApiId, { limit: 50 }),
  });

  // Create comment mutation
  const createCommentMutation = useMutation({
    mutationFn: (content: string) => createComment(questionApiId, { content }),
    onSuccess: () => {
      showToast("Success!", "Comment posted successfully.", "success");
      setNewComment("");
      queryClient.invalidateQueries({ queryKey: commentQueryKeys.list(questionApiId) });
    },
    onError: (error: Error) => {
      showToast("Error", error.message || "Failed to post comment.", "error");
    },
  });

  // Update comment mutation
  const updateCommentMutation = useMutation({
    mutationFn: ({ commentId, content }: { commentId: string; content: string }) => 
      updateComment(commentId, { content }),
    onSuccess: () => {
      showToast("Success!", "Comment updated successfully.", "success");
      queryClient.invalidateQueries({ queryKey: commentQueryKeys.list(questionApiId) });
    },
    onError: (error: Error) => {
      showToast("Error", error.message || "Failed to update comment.", "error");
    },
  });

  // Delete comment mutation
  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: string) => deleteComment(commentId),
    onSuccess: () => {
      showToast("Success!", "Comment deleted successfully.", "success");
      queryClient.invalidateQueries({ queryKey: commentQueryKeys.list(questionApiId) });
    },
    onError: (error: Error) => {
      showToast("Error", error.message || "Failed to delete comment.", "error");
    },
  });

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return;
    setIsSubmitting(true);
    try {
      await createCommentMutation.mutateAsync(newComment);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditComment = (commentId: string, newContent: string) => {
    updateCommentMutation.mutate({ commentId, content: newContent });
  };

  const handleDeleteComment = (commentId: string) => {
    if (window.confirm("Are you sure you want to delete this comment?")) {
      deleteCommentMutation.mutate(commentId);
    }
  };

  if (isLoading) {
    return (
      <Center py={8}>
        <Spinner size="lg" color="ui.primary" />
      </Center>
    );
  }

  if (error) {
    return (
      <Alert status="error" borderRadius="md">
        <AlertIcon />
        Failed to load comments. Please try again later.
      </Alert>
    );
  }

  const comments = commentsData?.comments || [];
  const hasComments = comments.length > 0;

  return (
    <Box
      bg={bgColor}
      backdropFilter="blur(10px)"
      border="1px solid"
      borderColor={borderColor}
      p={6}
      borderRadius="xl"
      boxShadow="md"
    >
      <Heading size="md" mb={4} color={textColor}>
        Comments ({comments.length})
      </Heading>

      {currentUser && (
        <Box mb={6}>
          <Textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            bg={bgColor}
            borderColor={borderColor}
            _hover={{
              borderColor: "ui.primary",
            }}
            _focus={{
              borderColor: "ui.primary",
              boxShadow: "0 0 0 1px var(--chakra-colors-ui-primary)",
            }}
            minH="100px"
            mb={3}
          />
          <Flex justify="flex-end">
            <Button
              variant="primary"
              onClick={handleSubmitComment}
              isLoading={isSubmitting || createCommentMutation.isPending}
              isDisabled={!newComment.trim()}
              _hover={{
                opacity: 0.9,
                bg: "ui.primary",
              }}
              transition="all 0.2s ease-in-out"
            >
              Post Comment
            </Button>
          </Flex>
        </Box>
      )}

      {hasComments ? (
        <VStack spacing={4} align="stretch">
          {comments.map((comment: Comment) => (
            <CommentItem
              key={comment.api_identifier}
              comment={comment}
              currentUserId={currentUser?.api_identifier}
              isAdmin={currentUser?.admin}
              onEdit={handleEditComment}
              onDelete={handleDeleteComment}
            />
          ))}
        </VStack>
      ) : (
        <Center py={8}>
          <Text color={textColor} fontSize="sm">
            No comments yet. Be the first to comment!
          </Text>
        </Center>
      )}

      {commentsData?.has_more && (
        <Center mt={4}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              // TODO: Implement pagination
              console.log("Load more comments");
            }}
          >
            Load more comments
          </Button>
        </Center>
      )}
    </Box>
  );
};

export default CommentSection;