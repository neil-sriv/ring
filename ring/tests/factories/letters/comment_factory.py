"""Factory for creating Comment instances in tests."""

from __future__ import annotations

import factory

from ring.letters.models.comment_model import Comment
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class CommentFactory(BaseFactory[Comment]):
    """Factory for creating test Comment instances."""

    class Meta:
        model = Comment

    content = factory.Faker("paragraph")
    question = factory.SubFactory(
        "ring.tests.factories.letters.question_factory.QuestionFactory"
    )
    author = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
