/**
 * Comment API client functions
 * This file contains manual API client functions for comment operations
 * until the OpenAPI spec is updated and client is regenerated.
 */

import { client } from './client.gen';

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
  try {
    const { data: responseData } = await client.post({
      url: '/letters/questions/{question_api_id}/comments',
      path: { question_api_id: questionApiId },
      body: data,
      security: [
        {
          scheme: 'bearer',
          type: 'http'
        }
      ],
      throwOnError: true
    });

    return responseData as Comment;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to create comment');
  }
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
  try {
    const { data } = await client.get({
      url: '/letters/questions/{question_api_id}/comments',
      path: { question_api_id: questionApiId },
      query: {
        skip: params?.skip || 0,
        limit: params?.limit || 50,
        include_deleted: params?.include_deleted || false,
      },
      security: [
        {
          scheme: 'bearer',
          type: 'http'
        }
      ],
      throwOnError: true
    });

    return data as CommentsResponse;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch comments');
  }
}

/**
 * Update a comment
 */
export async function updateComment(
  commentApiId: string,
  data: CommentUpdate
): Promise<Comment> {
  try {
    const { data: responseData } = await client.patch({
      url: '/letters/comments/{comment_api_id}',
      path: { comment_api_id: commentApiId },
      body: data,
      security: [
        {
          scheme: 'bearer',
          type: 'http'
        }
      ],
      throwOnError: true
    });

    return responseData as Comment;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to update comment');
  }
}

/**
 * Delete a comment
 */
export async function deleteComment(commentApiId: string): Promise<void> {
  try {
    await client.delete({
      url: '/letters/comments/{comment_api_id}',
      path: { comment_api_id: commentApiId },
      security: [
        {
          scheme: 'bearer',
          type: 'http'
        }
      ],
      throwOnError: true
    });
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to delete comment');
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