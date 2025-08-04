"""Tests for comment CRUD operations."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from ring.letters.crud import comment as comment_crud
from ring.letters.models.comment_model import Comment
from ring.tests.factories.letters.comment_factory import CommentFactory
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestCreateComment:
    """Test comment creation functionality."""

    def test_create_comment_success(self, db_session: Session) -> None:
        """Test successful comment creation."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        content = "This is a test comment on the question."
        comment = comment_crud.create_comment(
            db=db_session,
            question=question,
            author=user,
            content=content,
        )

        assert comment.content == content
        assert comment.author == user
        assert comment.question == question
        assert comment.api_identifier.startswith("com_")
        assert comment.deleted_at is None
        assert comment.deleted_by is None
        assert comment.updated_at is None

    def test_create_comment_with_long_content(
        self, db_session: Session
    ) -> None:
        """Test creating a comment with maximum allowed content length."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        # Create content at max length (5000 chars)
        content = "A" * 5000
        comment = comment_crud.create_comment(
            db=db_session,
            question=question,
            author=user,
            content=content,
        )

        assert len(comment.content) == 5000
        assert comment.content == content


class TestGetCommentsForQuestion:
    """Test retrieving comments for a question."""

    def test_get_comments_empty(self, db_session: Session) -> None:
        """Test getting comments when none exist."""
        question = QuestionFactory.create()
        db_session.commit()

        comments, total = comment_crud.get_comments_for_question(
            db=db_session,
            question_api_id=question.api_identifier,
        )

        assert comments == []
        assert total == 0

    def test_get_comments_multiple(self, db_session: Session) -> None:
        """Test getting multiple comments."""
        question = QuestionFactory.create()
        user1 = UserFactory.create()
        user2 = UserFactory.create()

        comment1 = CommentFactory.create(
            question=question, author=user1, content="First comment"
        )
        comment2 = CommentFactory.create(
            question=question, author=user2, content="Second comment"
        )
        comment3 = CommentFactory.create(
            question=question, author=user1, content="Third comment"
        )
        db_session.commit()

        comments, total = comment_crud.get_comments_for_question(
            db=db_session,
            question_api_id=question.api_identifier,
        )

        assert len(comments) == 3
        assert total == 3
        # Comments should be ordered by created_at
        assert comments[0].content == "First comment"
        assert comments[1].content == "Second comment"
        assert comments[2].content == "Third comment"

    def test_get_comments_exclude_deleted(self, db_session: Session) -> None:
        """Test that deleted comments are excluded by default."""
        question = QuestionFactory.create()
        user = UserFactory.create()

        comment1 = CommentFactory.create(
            question=question, author=user, content="Active comment"
        )
        comment2 = CommentFactory.create(
            question=question,
            author=user,
            content="Deleted comment",
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        comments, total = comment_crud.get_comments_for_question(
            db=db_session,
            question_api_id=question.api_identifier,
            include_deleted=False,
        )

        assert len(comments) == 1
        assert total == 1
        assert comments[0].content == "Active comment"

    def test_get_comments_include_deleted(self, db_session: Session) -> None:
        """Test including deleted comments."""
        question = QuestionFactory.create()
        user = UserFactory.create()

        comment1 = CommentFactory.create(
            question=question, author=user, content="Active comment"
        )
        comment2 = CommentFactory.create(
            question=question,
            author=user,
            content="Deleted comment",
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        comments, total = comment_crud.get_comments_for_question(
            db=db_session,
            question_api_id=question.api_identifier,
            include_deleted=True,
        )

        assert len(comments) == 2
        assert total == 2

    def test_get_comments_pagination(self, db_session: Session) -> None:
        """Test comment pagination."""
        question = QuestionFactory.create()
        user = UserFactory.create()

        # Create 10 comments
        for i in range(10):
            CommentFactory.create(
                question=question,
                author=user,
                content=f"Comment {i}",
            )
        db_session.commit()

        # Get first page
        comments_page1, total = comment_crud.get_comments_for_question(
            db=db_session,
            question_api_id=question.api_identifier,
            skip=0,
            limit=5,
        )

        assert len(comments_page1) == 5
        assert total == 10

        # Get second page
        comments_page2, _ = comment_crud.get_comments_for_question(
            db=db_session,
            question_api_id=question.api_identifier,
            skip=5,
            limit=5,
        )

        assert len(comments_page2) == 5
        # Ensure no overlap
        page1_ids = {c.id for c in comments_page1}
        page2_ids = {c.id for c in comments_page2}
        assert page1_ids.isdisjoint(page2_ids)


class TestUpdateComment:
    """Test comment update functionality."""

    def test_update_comment_content(self, db_session: Session) -> None:
        """Test updating comment content."""
        comment = CommentFactory.create(content="Original content")
        db_session.commit()

        new_content = "Updated content"
        updated_comment = comment_crud.update_comment(
            db=db_session,
            comment=comment,
            content=new_content,
        )

        assert updated_comment.content == new_content
        assert updated_comment.updated_at is not None
        assert updated_comment.id == comment.id

    def test_update_deleted_comment_fails(self, db_session: Session) -> None:
        """Test that updating a deleted comment fails."""
        user = UserFactory.create()
        comment = CommentFactory.create(
            content="Original content",
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        with pytest.raises(ValueError, match="Cannot edit deleted comment"):
            comment_crud.update_comment(
                db=db_session,
                comment=comment,
                content="New content",
            )


class TestSoftDeleteComment:
    """Test comment soft deletion."""

    def test_soft_delete_comment(self, db_session: Session) -> None:
        """Test soft deleting a comment."""
        admin = UserFactory.create(admin=True)
        comment = CommentFactory.create()
        db_session.commit()

        deleted_comment = comment_crud.soft_delete_comment(
            db=db_session,
            comment=comment,
            deleted_by=admin,
        )

        assert deleted_comment.deleted_at is not None
        assert deleted_comment.deleted_by == admin
        assert deleted_comment.is_deleted is True

    def test_soft_delete_already_deleted_comment(
        self, db_session: Session
    ) -> None:
        """Test soft deleting an already deleted comment."""
        admin = UserFactory.create(admin=True)
        comment = CommentFactory.create(
            deleted_at=datetime.now(),
            deleted_by=admin,
        )
        db_session.commit()

        # Should not raise an error, just return the comment
        deleted_comment = comment_crud.soft_delete_comment(
            db=db_session,
            comment=comment,
            deleted_by=admin,
        )

        assert deleted_comment.is_deleted is True


class TestPermissionChecks:
    """Test permission check functions."""

    def test_can_user_edit_own_comment(self, db_session: Session) -> None:
        """Test that users can edit their own comments."""
        user = UserFactory.create()
        comment = CommentFactory.create(author=user)
        db_session.commit()

        assert comment_crud.can_user_edit_comment(user, comment) is True

    def test_can_user_edit_others_comment(self, db_session: Session) -> None:
        """Test that users cannot edit others' comments."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        comment = CommentFactory.create(author=user1)
        db_session.commit()

        assert comment_crud.can_user_edit_comment(user2, comment) is False

    def test_can_user_edit_deleted_comment(self, db_session: Session) -> None:
        """Test that users cannot edit deleted comments."""
        user = UserFactory.create()
        comment = CommentFactory.create(
            author=user,
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        assert comment_crud.can_user_edit_comment(user, comment) is False

    def test_can_admin_delete_comment(self, db_session: Session) -> None:
        """Test that admins can delete comments."""
        admin = UserFactory.create(admin=True)
        user = UserFactory.create()
        comment = CommentFactory.create(author=user)
        db_session.commit()

        assert comment_crud.can_user_delete_comment(admin, comment) is True

    def test_can_regular_user_delete_comment(
        self, db_session: Session
    ) -> None:
        """Test that regular users cannot delete comments."""
        user = UserFactory.create(admin=False)
        comment = CommentFactory.create(author=user)
        db_session.commit()

        assert comment_crud.can_user_delete_comment(user, comment) is False

    def test_get_comment_for_user_in_group(self, db_session: Session) -> None:
        """Test getting a comment when user is in the group."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(question=question)
        db_session.commit()

        result = comment_crud.get_comment_for_user(
            db=db_session,
            user=user,
            comment_api_id=comment.api_identifier,
        )

        assert result == comment

    def test_get_comment_for_user_not_in_group(
        self, db_session: Session
    ) -> None:
        """Test getting a comment when user is not in the group."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        group = GroupFactory.create(admin=user1)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(question=question)
        db_session.commit()

        result = comment_crud.get_comment_for_user(
            db=db_session,
            user=user2,
            comment_api_id=comment.api_identifier,
        )

        assert result is None

    def test_get_comment_for_user_deleted_comment(
        self, db_session: Session
    ) -> None:
        """Test getting a deleted comment returns None for regular users."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            deleted_at=datetime.now(),
            deleted_by=user,
        )
        db_session.commit()

        result = comment_crud.get_comment_for_user(
            db=db_session,
            user=user,
            comment_api_id=comment.api_identifier,
        )

        assert result is None

    def test_get_comment_for_admin_deleted_comment(
        self, db_session: Session
    ) -> None:
        """Test getting a deleted comment returns the comment for admins."""
        admin = UserFactory.create(admin=True)
        group = GroupFactory.create(admin=admin)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        comment = CommentFactory.create(
            question=question,
            deleted_at=datetime.now(),
            deleted_by=admin,
        )
        db_session.commit()

        result = comment_crud.get_comment_for_user(
            db=db_session,
            user=admin,
            comment_api_id=comment.api_identifier,
        )

        assert result == comment
