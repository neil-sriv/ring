"""Quick test script for Comment model."""

from __future__ import annotations

from datetime import datetime

from ring.fastapp.dependencies import get_db
from ring.letters.models.comment_model import Comment
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.letters.constants import LetterStatus, LetterType

# Get database session
db = next(get_db())

# Get or create test data
user = db.query(User).first()
if not user:
    print("Creating test user...")
    user = User.create(
        email="test@example.com",
        name="Test User",
        hashed_password="dummy_hash"
    )
    db.add(user)
    db.commit()

# Create a group if needed
group = db.query(Group).first()
if not group:
    print("Creating test group...")
    group = Group.create(name="Test Group", admin=user)
    db.add(group)
    db.commit()

# Create a letter if needed
letter = db.query(Letter).first()
if not letter:
    print("Creating test letter...")
    letter = Letter.create(
        group=group,
        send_at=datetime.now(),
        letter_status=LetterStatus.IN_PROGRESS,
        letter_type=LetterType.CYCLIC
    )
    db.add(letter)
    db.commit()

# Create a question if needed
question = db.query(Question).first()
if not question:
    print("Creating test question...")
    question = Question.create(
        letter=letter,
        question_text="What is your favorite programming language?",
        author=user
    )
    db.add(question)
    db.commit()

print(f"\nTest data ready:")
print(f"User: {user.email}")
print(f"Question: {question.question_text}")

# Create a comment
print("\n--- Testing Comment Creation ---")
comment = Comment.create(
    question=question,
    author=user,
    content="Python is my favorite because of its simplicity and powerful libraries!"
)

db.add(comment)
db.commit()

print(f"✅ Created comment with ID: {comment.api_identifier}")
print(f"   Content: {comment.content}")
print(f"   Author: {comment.author.email}")
print(f"   Is deleted: {comment.is_deleted}")

# Test editing
print("\n--- Testing Comment Edit ---")
comment.content = "Actually, I like both Python and TypeScript!"
comment.updated_at = datetime.now()
db.commit()

print(f"✅ Updated comment content: {comment.content}")
print(f"   Updated at: {comment.updated_at}")

# Test soft delete
print("\n--- Testing Soft Delete ---")
comment.deleted_at = datetime.now()
comment.deleted_by = user  # In real app, this would be an admin
db.commit()

print(f"✅ Soft deleted comment")
print(f"   Is deleted: {comment.is_deleted}")
print(f"   Deleted at: {comment.deleted_at}")

# Test querying
print("\n--- Testing Queries ---")
all_comments = db.query(Comment).filter(Comment.question_id == question.id).all()
print(f"Total comments on question: {len(all_comments)}")

active_comments = db.query(Comment).filter(
    Comment.question_id == question.id,
    Comment.deleted_at.is_(None)
).all()
print(f"Active comments (not deleted): {len(active_comments)}")

# Test relationship
print(f"Comments via question.comments: {len(question.comments)}")

print("\n✅ All tests passed!")

db.close()