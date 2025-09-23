"""Document factories for test data generation.

This module provides factory classes for creating test data for document-related models,
including Document and DocumentEdit models.
"""

from __future__ import annotations

import factory

from ring.notebook.models.document import Document, DocumentEdit
from ring.tests.factories.base_factory import BaseFactory, register_factory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


@register_factory
class DocumentFactory(BaseFactory[Document]):
    """Factory for creating Document test instances."""

    class Meta:
        model = Document

    name = factory.Faker("sentence", nb_words=3)
    latest_snapshot_version = factory.Sequence(lambda n: n + 1)
    content = factory.LazyFunction(lambda: b"Default test content")
    group = factory.SubFactory(GroupFactory)


@register_factory
class DocumentEditFactory(BaseFactory[DocumentEdit]):
    """Factory for creating DocumentEdit test instances."""

    class Meta:
        model = DocumentEdit

    delta = factory.Faker("text", max_nb_chars=100)
    document = factory.SubFactory(DocumentFactory)
    author = factory.SubFactory(UserFactory)

    @factory.post_generation
    def delta(obj, create: bool, extracted: str | None, **kwargs) -> None:
        """Convert string delta to bytes for storage."""
        if extracted is not None:
            obj.delta = extracted.encode("utf-8")
        elif isinstance(obj.delta, str):
            obj.delta = obj.delta.encode("utf-8")
