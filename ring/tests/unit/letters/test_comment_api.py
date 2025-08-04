"""Tests for comment API endpoints."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.models.comment_model import Comment
from ring.parties.models.user_model import User
from ring.tests.factories.letters.comment_factory import CommentFactory
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.conftest import TClientForUser


class TestCreateCommentEndpoint:
    """Test the POST /letters/questions/{question_api_id}/comments endpoint."""

    def test_create_comment_success(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test successful comment creation."""
        # Create a group with the current user as admin and member
        group = GroupFactory.create(admin=current_user)
        group.members.append(current_user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        response = authenticated_client.post(
            f"/letters/questions/{question.api_identifier}/comments",
            json={"content": "This is a test comment"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["author"]["api_identifier"] == current_user.api_identifier
        assert data["question"]["api_identifier"] == question.api_identifier
        assert "api_identifier" in data
        assert data["api_identifier"].startswith("com_")

    def test_create_comment_user_not_in_group(
        self,
        get_client_for_user: TClientForUser,
        db_session: Session,
    ) -> None:
        """Test that users not in the group cannot comment."""
        # Create a group with user1 as admin
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        group = GroupFactory.create(admin=user1)
        group.members.append(user1)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        # Use user2 who is not in the group
        client = get_client_for_user(user2)
        response = client.post(
            f"/letters/questions/{question.api_identifier}/comments",
            json={"content": "This should fail"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_comment_empty_content(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that empty content is rejected."""
        group = GroupFactory.create(admin=current_user)
        group.members.append(current_user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        response = authenticated_client.post(
            f"/letters/questions/{question.api_identifier}/comments",
            json={"content": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_comment_content_too_long(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that content over 5000 chars is rejected."""
        group = GroupFactory.create(admin=current_user)
        group.members.append(current_user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        response = authenticated_client.post(
            f"/letters/questions/{question.api_identifier}/comments",
            json={"content": "A" * 5001},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_comment_nonexistent_question(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test creating comment on nonexistent question."""
        response = authenticated_client.post(
            "/letters/questions/que_nonexistent/comments",
            json={"content": "This should fail"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetCommentsEndpoint:
    """Test the GET /letters/questions/{question_api_id}/comments endpoint."""

    def test_get_comments_success(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test successful retrieval of comments."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)

        comment1 = CommentFactory.create(
            question=question,
            author=user,
            content="First comment",
        )
        comment2 = CommentFactory.create(
            question=question,
            author=user,
            content="Second comment",
        )
        db_session.commit()

        response = authenticated_client.get(
            f"/letters/questions/{question.api_identifier}/comments",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["comments"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 50
        assert data["has_more"] is False

    def test_get_comments_pagination(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test comment pagination."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)

        # Create 10 comments
        for i in range(10):
            CommentFactory.create(
                question=question,
                author=user,
                content=f"Comment {i}",
            )
        db_session.commit()

        # Get first page
        response = authenticated_client.get(
            f"/letters/questions/{question.api_identifier}/comments?skip=0&limit=5",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 10
        assert len(data["comments"]) == 5
        assert data["has_more"] is True

    def test_get_comments_exclude_deleted(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that deleted comments are excluded for regular users."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)

        comment1 = CommentFactory.create(
            question=question,
            author=user,
            content="Active comment",
        )
        comment2 = CommentFactory.create(
            question=question,
            author=user,
            content="Deleted comment",
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        response = authenticated_client.get(
            f"/letters/questions/{question.api_identifier}/comments",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["comments"]) == 1
        assert data["comments"][0]["content"] == "Active comment"

    def test_get_comments_include_deleted_admin_only(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that only admins can see deleted comments."""
        admin = UserFactory.create(admin=True)
        regular_user = UserFactory.create(admin=False)
        group = GroupFactory.create(admin=admin)
        group.members.append(regular_user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)

        comment = CommentFactory.create(
            question=question,
            author=regular_user,
            content="Deleted comment",
            deleted_at=datetime.now(),
            deleted_by=admin,
        )
        db_session.commit()

        # Test with regular user
        mock_auth_dependencies.return_value.current_user = regular_user
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.get(
            f"/letters/questions/{question.api_identifier}/comments?include_deleted=true",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test with admin
        mock_auth_dependencies.return_value.current_user = admin
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.get(
            f"/letters/questions/{question.api_identifier}/comments?include_deleted=true",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1

    def test_get_comments_user_not_in_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that users not in group cannot see comments."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        group = GroupFactory.create(admin=user1)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        mock_auth_dependencies.return_value.current_user = user2
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.get(
            f"/letters/questions/{question.api_identifier}/comments",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateCommentEndpoint:
    """Test the PATCH /letters/comments/{comment_api_id} endpoint."""

    def test_update_comment_success(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test successful comment update by author."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=user,
            content="Original content",
        )
        db_session.commit()

        response = authenticated_client.patch(
            f"/letters/comments/{comment.api_identifier}",
            json={"content": "Updated content"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["updated_at"] is not None

    def test_update_comment_not_author(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that non-authors cannot update comments."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        group = GroupFactory.create(admin=user1)
        group.members.append(user2)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=user1,
            content="Original content",
        )
        db_session.commit()

        mock_auth_dependencies.return_value.current_user = user2
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.patch(
            f"/letters/comments/{comment.api_identifier}",
            json={"content": "This should fail"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_deleted_comment(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that deleted comments cannot be updated."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=user,
            content="Original content",
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        response = authenticated_client.patch(
            f"/letters/comments/{comment.api_identifier}",
            json={"content": "This should fail"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_comment_empty_content(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that empty content is rejected."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=user,
            content="Original content",
        )
        db_session.commit()

        response = authenticated_client.patch(
            f"/letters/comments/{comment.api_identifier}",
            json={"content": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeleteCommentEndpoint:
    """Test the DELETE /letters/comments/{comment_api_id} endpoint."""

    def test_delete_comment_admin_success(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test successful comment deletion by admin."""
        admin = UserFactory.create(admin=True)
        regular_user = UserFactory.create()
        group = GroupFactory.create(admin=admin)
        group.members.append(regular_user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=regular_user,
            content="Comment to delete",
        )
        db_session.commit()

        mock_auth_dependencies.return_value.current_user = admin
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.delete(
            f"/letters/comments/{comment.api_identifier}",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Comment deleted successfully"

        # Verify the comment is soft deleted
        db_session.refresh(comment)
        assert comment.is_deleted is True
        assert comment.deleted_by == admin

    def test_delete_comment_regular_user_fails(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that regular users cannot delete comments."""
        user = UserFactory.create(admin=False)
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=user,
            content="Own comment",
        )
        db_session.commit()

        response = authenticated_client.delete(
            f"/letters/comments/{comment.api_identifier}",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_already_deleted_comment(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test deleting an already deleted comment."""
        admin = UserFactory.create(admin=True)
        group = GroupFactory.create(admin=admin)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            author=admin,
            content="Already deleted",
            deleted_at=datetime.now(),
            deleted_by=admin,
        )
        db_session.commit()

        mock_auth_dependencies.return_value.current_user = admin
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.delete(
            f"/letters/comments/{comment.api_identifier}",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_comment_user_not_in_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that users not in group cannot delete comments."""
        admin1 = UserFactory.create(admin=True)
        admin2 = UserFactory.create(admin=True)
        group = GroupFactory.create(admin=admin1)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(question=question)
        db_session.commit()

        mock_auth_dependencies.return_value.current_user = admin2
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.delete(
            f"/letters/comments/{comment.api_identifier}",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCommentAuthorizationIntegration:
    """Integration tests for comment authorization."""

    def test_comment_hierarchy_permissions(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """Test that comment permissions follow the group hierarchy."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        group1 = GroupFactory.create(admin=user1)
        group2 = GroupFactory.create(admin=user2)

        letter1 = LetterFactory.create(group=group1)
        question1 = QuestionFactory.create(letter=letter1)
        comment1 = CommentFactory.create(
            question=question1,
            author=user1,
            content="Comment in group1",
        )

        letter2 = LetterFactory.create(group=group2)
        question2 = QuestionFactory.create(letter=letter2)
        comment2 = CommentFactory.create(
            question=question2,
            author=user2,
            content="Comment in group2",
        )
        db_session.commit()

        # User1 can see comments in group1 but not group2
        mock_auth_dependencies.return_value.current_user = user1
        mock_auth_dependencies.return_value.db = db_session

        response = authenticated_client.get(
            f"/letters/questions/{question1.api_identifier}/comments",
        )
        assert response.status_code == status.HTTP_200_OK

        response = authenticated_client.get(
            f"/letters/questions/{question2.api_identifier}/comments",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
