"""Tests for the Comment model.

This module tests the Comment SQLAlchemy model to ensure it functions
correctly with the database and follows expected patterns.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from ring.letters.models.comment_model import Comment
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.user_factory import UserFactory


def test_create_comment(db: Session) -> None:
    """Test creating a basic comment."""
    # Create test data
    user = UserFactory()
    letter = LetterFactory()
    question = QuestionFactory(letter=letter)
    
    # Create comment
    comment = Comment.create(
        question=question,
        author=user,
        content="This is a test comment on the question!"
    )
    
    db.add(comment)
    db.commit()
    
    # Verify comment was created
    assert comment.id is not None
    assert comment.api_identifier.startswith("com_")
    assert comment.content == "This is a test comment on the question!"
    assert comment.author == user
    assert comment.question == question
    assert comment.created_at is not None
    assert comment.updated_at is None
    assert comment.deleted_at is None
    assert comment.is_deleted is False


def test_comment_soft_delete(db: Session) -> None:
    """Test soft deleting a comment."""
    # Create test data
    user = UserFactory()
    admin = UserFactory()
    letter = LetterFactory()
    question = QuestionFactory(letter=letter)
    
    # Create comment
    comment = Comment.create(
        question=question,
        author=user,
        content="This comment will be deleted"
    )
    
    db.add(comment)
    db.commit()
    
    # Soft delete the comment
    comment.deleted_at = datetime.now()
    comment.deleted_by = admin
    db.commit()
    
    # Verify soft delete
    assert comment.is_deleted is True
    assert comment.deleted_at is not None
    assert comment.deleted_by == admin
    

def test_comment_edit(db: Session) -> None:
    """Test editing a comment."""
    # Create test data
    user = UserFactory()
    letter = LetterFactory()
    question = QuestionFactory(letter=letter)
    
    # Create comment
    comment = Comment.create(
        question=question,
        author=user,
        content="Original content"
    )
    
    db.add(comment)
    db.commit()
    
    # Edit the comment
    comment.content = "Updated content"
    comment.updated_at = datetime.now()
    db.commit()
    
    # Verify edit
    assert comment.content == "Updated content"
    assert comment.updated_at is not None


def test_comment_relationships(db: Session) -> None:
    """Test comment relationships are properly established."""
    # Create test data
    user = UserFactory()
    letter = LetterFactory()
    question = QuestionFactory(letter=letter)
    
    # Create multiple comments
    comment1 = Comment.create(question=question, author=user, content="First comment")
    comment2 = Comment.create(question=question, author=user, content="Second comment")
    
    db.add_all([comment1, comment2])
    db.commit()
    
    # Verify relationships
    assert len(question.comments) == 2
    assert comment1 in question.comments
    assert comment2 in question.comments
    assert comment1.question == question
    assert comment2.question == question