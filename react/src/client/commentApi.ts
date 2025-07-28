/**
 * Comment API client functions
 * This file contains manual API client functions for comment operations
 * until the OpenAPI spec is updated and client is regenerated.
 */

import { client } from './sdk.gen';

export interface CommentCreate {
  content: string;
}

export interface CommentUpdate {
  content: string;
}

export interface Comment {
  api_identifier: string;
  content: string;
  created_at: string;
  updated_at?: string;
  author: {
    api_identifier: string;
    name: string;
    email: string;
  };
  question: {
    api_identifier: string;
    question_text: string;
  };
  is_deleted: boolean;
}

export interface CommentsResponse {
  comments: Comment[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

/**
 * Create a comment on a question
 */
export async function createComment(
  questionApiId: string,
  data: CommentCreate
): Promise<Comment> {
  const response = await client.POST('/letters/questions/{question_api_id}/comments', {
    params: {
      path: { question_api_id: questionApiId },
    },
    body: data,
  });

  if (response.error) {
    throw new Error(response.error.detail || 'Failed to create comment');
  }

  return response.data as Comment;
}

/**
 * Get comments for a question
 */
export async function getComments(
  questionApiId: string,
  params?: {
    skip?: number;
    limit?: number;
    include_deleted?: boolean;
  }
): Promise<CommentsResponse> {
  const response = await client.GET('/letters/questions/{question_api_id}/comments', {
    params: {
      path: { question_api_id: questionApiId },
      query: {
        skip: params?.skip || 0,
        limit: params?.limit || 50,
        include_deleted: params?.include_deleted || false,
      },
    },
  });

  if (response.error) {
    throw new Error(response.error.detail || 'Failed to fetch comments');
  }

  return response.data as CommentsResponse;
}

/**
 * Update a comment
 */
export async function updateComment(
  commentApiId: string,
  data: CommentUpdate
): Promise<Comment> {
  const response = await client.PATCH('/letters/comments/{comment_api_id}', {
    params: {
      path: { comment_api_id: commentApiId },
    },
    body: data,
  });

  if (response.error) {
    throw new Error(response.error.detail || 'Failed to update comment');
  }

  return response.data as Comment;
}

/**
 * Delete a comment
 */
export async function deleteComment(commentApiId: string): Promise<void> {
  const response = await client.DELETE('/letters/comments/{comment_api_id}', {
    params: {
      path: { comment_api_id: commentApiId },
    },
  });

  if (response.error) {
    throw new Error(response.error.detail || 'Failed to delete comment');
  }
}

/**
 * TanStack Query keys for comment queries
 */
export const commentQueryKeys = {
  all: ['comments'] as const,
  lists: () => [...commentQueryKeys.all, 'list'] as const,
  list: (questionApiId: string, params?: any) =>
    [...commentQueryKeys.lists(), questionApiId, params] as const,
  details: () => [...commentQueryKeys.all, 'detail'] as const,
  detail: (commentApiId: string) =>
    [...commentQueryKeys.details(), commentApiId] as const,
};