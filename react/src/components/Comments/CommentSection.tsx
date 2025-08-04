import { useState } from "react";
import {
  Box,
  VStack,
  Text,
  Textarea,
  Button,
  Divider,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserLinked } from "../../client";
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen";
import { getComments, createComment, commentQueryKeys } from "../../client/commentApi";
// Comment types will be added after API client generation
import CommentItem from "./CommentItem";

interface CommentSectionProps {
  questionApiId: string;
}

export default function CommentSection({ questionApiId }: CommentSectionProps) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
  const [newComment, setNewComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch comments
  const { data: commentsData, isLoading, error } = useQuery({
    queryKey: commentQueryKeys.list(questionApiId, { limit: 50 }),
    queryFn: async () => {
      return await getComments(questionApiId, { limit: 50 });
    },
  });

  // Create comment mutation
  const createCommentMutation = useMutation({
    mutationFn: async (content: string) => {
      return await createComment(questionApiId, { content });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commentQueryKeys.list(questionApiId) });
      setNewComment("");
      toast({
        title: "Comment added",
        status: "success",
        duration: 3000,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to add comment",
        description: error.response?.data?.detail || "Something went wrong",
        status: "error",
        duration: 5000,
      });
    },
  });

  const handleSubmit = async () => {
    if (!newComment.trim()) return;
    
    setIsSubmitting(true);
    try {
      await createCommentMutation.mutateAsync(newComment);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Box py={8} textAlign="center">
        <Spinner size="lg" />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert status="error" borderRadius="md">
        <AlertIcon />
        Failed to load comments
      </Alert>
    );
  }

  const comments = commentsData?.comments || [];
  const totalComments = commentsData?.total || 0;

  return (
    <VStack spacing={6} align="stretch" mt={8}>
      <Divider />
      
      <Box>
        <Text fontSize="xl" fontWeight="bold" mb={4}>
          Discussion ({totalComments} {totalComments === 1 ? "comment" : "comments"})
        </Text>

        {/* Add comment form */}
        {currentUser && (
          <Box mb={6}>
            <Textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              resize="vertical"
              minH="100px"
              mb={2}
            />
            <Button
              colorScheme="blue"
              size="sm"
              onClick={handleSubmit}
              isLoading={isSubmitting}
              isDisabled={!newComment.trim()}
            >
              Post Comment
            </Button>
          </Box>
        )}

        {/* Comments list */}
        <VStack spacing={4} align="stretch">
          {comments.length === 0 ? (
            <Text color="gray.500" textAlign="center" py={8}>
              No comments yet. Be the first to start the discussion!
            </Text>
          ) : (
            comments.map((comment: any) => (
              <CommentItem
                key={comment.api_identifier}
                comment={comment}
                questionApiId={questionApiId}
              />
            ))
          )}
        </VStack>

        {/* Load more button if needed */}
        {commentsData?.has_more && (
          <Box textAlign="center" mt={4}>
            <Button variant="outline" size="sm">
              Load More Comments
            </Button>
          </Box>
        )}
      </Box>
    </VStack>
  );
}