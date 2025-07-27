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

    @factory.lazy_attribute
    def content(self):
        return factory.Faker("paragraph").generate({})

    @factory.lazy_attribute
    def question(self):
        from ring.tests.factories.letters.question_factory import QuestionFactory
        return QuestionFactory.create()

    @factory.lazy_attribute
    def author(self):
        from ring.tests.factories.parties.user_factory import UserFactory
        return UserFactory.create()
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to use Comment.create method."""
        # Extract the fields we need for Comment.create
        question = kwargs.pop('question')
        author = kwargs.pop('author')
        content = kwargs.pop('content')
        
        # Create the comment using the model's create method
        comment = Comment.create(
            question=question,
            author=author,
            content=content
        )
        
        # Apply any additional attributes
        for key, value in kwargs.items():
            setattr(comment, key, value)
        
        return comment