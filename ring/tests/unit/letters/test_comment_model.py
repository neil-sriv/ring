"""Tests for the Comment model."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from ring.letters.models.comment_model import Comment
from ring.tests.factories.letters.comment_factory import CommentFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestCommentModel:
    """Test the Comment model."""

    def test_comment_creation(self, db_session: Session) -> None:
        """Test creating a comment."""
        user = UserFactory.create()
        question = QuestionFactory.create()
        db_session.commit()

        comment = Comment.create(
            question=question,
            author=user,
            content="This is a test comment",
        )
        db_session.add(comment)
        db_session.commit()

        assert comment.id is not None
        assert comment.api_identifier.startswith("com_")
        assert comment.content == "This is a test comment"
        assert comment.author == user
        assert comment.question == question
        assert comment.created_at is not None
        assert comment.updated_at is None
        assert comment.deleted_at is None
        assert comment.deleted_by is None

    def test_comment_relationships(self, db_session: Session) -> None:
        """Test comment relationships."""
        user = UserFactory.create()
        question = QuestionFactory.create()
        comment = CommentFactory.create(
            question=question,
            author=user,
        )
        db_session.commit()

        # Test author relationship
        assert comment.author == user
        assert comment in user.comments

        # Test question relationship
        assert comment.question == question
        assert comment in question.comments

    def test_comment_soft_delete(self, db_session: Session) -> None:
        """Test soft delete functionality."""
        admin = UserFactory.create(admin=True)
        comment = CommentFactory.create()
        db_session.commit()

        assert comment.is_deleted is False

        # Soft delete the comment
        comment.deleted_at = datetime.now()
        comment.deleted_by = admin
        db_session.commit()

        assert comment.is_deleted is True
        assert comment.deleted_by == admin

    def test_comment_update(self, db_session: Session) -> None:
        """Test updating a comment."""
        comment = CommentFactory.create(content="Original content")
        db_session.commit()

        # Update the comment
        comment.content = "Updated content"
        comment.updated_at = datetime.now()
        db_session.commit()

        assert comment.content == "Updated content"
        assert comment.updated_at is not None

    def test_comment_cascade_on_question_delete(
        self, db_session: Session
    ) -> None:
        """Test that comments are deleted when question is deleted."""
        question = QuestionFactory.create()
        comment = CommentFactory.create(question=question)
        db_session.commit()

        comment_id = comment.id

        # Delete the question
        db_session.delete(question)
        db_session.commit()

        # Comment should be gone
        assert (
            db_session.query(Comment).filter_by(id=comment_id).first() is None
        )

    def test_comment_not_cascade_on_author_delete(
        self, db_session: Session
    ) -> None:
        """Test that comments remain when author is deleted."""
        user = UserFactory.create()
        comment = CommentFactory.create(author=user)
        db_session.commit()

        comment_id = comment.id

        # Delete the user
        db_session.delete(user)
        db_session.commit()

        # Comment should still exist but with null author
        comment = db_session.query(Comment).filter_by(id=comment_id).first()
        assert comment is not None
        assert comment.author_id is None

    def test_comment_api_identifier_unique(self, db_session: Session) -> None:
        """Test that API identifiers are unique."""
        comment1 = CommentFactory.create()
        comment2 = CommentFactory.create()
        db_session.commit()

        assert comment1.api_identifier != comment2.api_identifier
        assert comment1.api_identifier.startswith("com_")
        assert comment2.api_identifier.startswith("com_")

    def test_comment_content_required(self, db_session: Session) -> None:
        """Test that content is required."""
        with pytest.raises(Exception):
            comment = Comment.create(
                question=QuestionFactory.create(),
                author=UserFactory.create(),
                content=None,  # This should fail
            )
            db_session.add(comment)
            db_session.commit()

    def test_comment_pydantic_dict(self, db_session: Session) -> None:
        """Test the pydantic_dict method."""
        user = UserFactory.create()
        question = QuestionFactory.create()
        comment = CommentFactory.create(
            question=question,
            author=user,
            content="Test comment",
        )
        db_session.commit()

        # Test unlinked dict
        unlinked_dict = comment.pydantic_dict()
        assert unlinked_dict["api_identifier"] == comment.api_identifier
        assert unlinked_dict["content"] == "Test comment"
        assert unlinked_dict["created_at"] == comment.created_at
        assert unlinked_dict["updated_at"] is None
        assert unlinked_dict["deleted_at"] is None
        assert "author" not in unlinked_dict
        assert "question" not in unlinked_dict

        # Test linked dict
        linked_dict = comment.pydantic_dict(is_linked=True)
        assert linked_dict["api_identifier"] == comment.api_identifier
        assert linked_dict["content"] == "Test comment"
        assert linked_dict["author"]["api_identifier"] == user.api_identifier
        assert (
            linked_dict["question"]["api_identifier"]
            == question.api_identifier
        )
        assert "deleted_by" in linked_dict

    def test_comment_timestamps(self, db_session: Session) -> None:
        """Test that timestamps work correctly."""
        comment = CommentFactory.create()
        db_session.commit()

        created_at = comment.created_at
        assert created_at is not None

        # Update the comment
        comment.content = "Updated"
        comment.updated_at = datetime.now()
        db_session.commit()

        assert comment.created_at == created_at  # Should not change
        assert comment.updated_at is not None
        assert comment.updated_at > comment.created_at

    def test_multiple_comments_on_question(self, db_session: Session) -> None:
        """Test multiple comments on the same question."""
        question = QuestionFactory.create()
        user1 = UserFactory.create()
        user2 = UserFactory.create()

        comment1 = CommentFactory.create(
            question=question,
            author=user1,
            content="First comment",
        )
        comment2 = CommentFactory.create(
            question=question,
            author=user2,
            content="Second comment",
        )
        comment3 = CommentFactory.create(
            question=question,
            author=user1,
            content="Third comment",
        )
        db_session.commit()

        assert len(question.comments) == 3
        assert comment1 in question.comments
        assert comment2 in question.comments
        assert comment3 in question.comments
