"""Tests for candidate-scoped enforcer loading used by filter_to_authorized."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from ring.authz.authz import (
    InaccessibleResource,
    bulk_can_or_inaccessible,
    can,
    filter_to_authorized,
)
from ring.authz.enforcer import Action, build_stateless_enforcer
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_sqlalchemy_object_list_equal_with_order_insensitive,
)


@pytest.fixture
def hierarchy_fixture(db_session: Session) -> dict[str, Any]:
    member = UserFactory.create()
    other_member = UserFactory.create()
    outsider = UserFactory.create()

    group_a = GroupFactory.create(admin=member, members=[member, other_member])
    letter_a = LetterFactory.create(group=group_a)
    question_a = QuestionFactory.create(letter=letter_a)
    response_a = ResponseFactory.create(
        question=question_a, participant=member
    )

    group_b = GroupFactory.create(admin=outsider)
    letter_b = LetterFactory.create(group=group_b)
    question_b = QuestionFactory.create(letter=letter_b)
    response_b = ResponseFactory.create(
        question=question_b, participant=outsider
    )

    db_session.commit()

    return {
        "member": member,
        "other_member": other_member,
        "outsider": outsider,
        "group_a": group_a,
        "letter_a": letter_a,
        "question_a": question_a,
        "response_a": response_a,
        "group_b": group_b,
        "letter_b": letter_b,
        "question_b": question_b,
        "response_b": response_b,
    }


def _filter_with_full_enforcer(
    db: Session,
    user: Any,
    action: Action,
    resources: list[Any],
) -> list[Any]:
    """Reference filter using a fully loaded enforcer (outcome oracle)."""
    enforcer = build_stateless_enforcer(db, user.api_identifier)
    return [
        resource
        for resource in resources
        if can(db, user, action, resource, enforcer)
    ]


class TestScopedFilterEquivalence:
    def test_filter_matches_full_enforcer_mixed_resources(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]
        resources = [
            hierarchy_fixture["group_a"],
            hierarchy_fixture["letter_a"],
            hierarchy_fixture["question_a"],
            hierarchy_fixture["response_a"],
            hierarchy_fixture["other_member"],
            hierarchy_fixture["group_b"],
            hierarchy_fixture["letter_b"],
            hierarchy_fixture["question_b"],
            hierarchy_fixture["response_b"],
            hierarchy_fixture["outsider"],
        ]

        scoped = filter_to_authorized(
            db_session, member, Action.READ, resources
        )
        full = _filter_with_full_enforcer(
            db_session, member, Action.READ, resources
        )

        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            list(scoped), full
        )

    def test_bulk_can_or_inaccessible_matches_full_enforcer(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]
        resources = [
            hierarchy_fixture["letter_a"],
            hierarchy_fixture["letter_b"],
            hierarchy_fixture["response_a"],
            hierarchy_fixture["other_member"],
        ]

        scoped = bulk_can_or_inaccessible(
            db_session, member, Action.READ, resources
        )
        enforcer = build_stateless_enforcer(db_session, member.api_identifier)
        expected = [
            resource
            if can(db_session, member, Action.READ, resource, enforcer)
            else InaccessibleResource(resource)
            for resource in resources
        ]

        assert len(scoped) == len(expected)
        for got, want in zip(scoped, expected, strict=True):
            if isinstance(want, InaccessibleResource):
                assert isinstance(got, InaccessibleResource)
                assert got.resource is want.resource
            else:
                assert got is want


class TestEmptyFilterEarlyReturn:
    def test_empty_resources_skips_full_and_scoped_loaders(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        db_session.commit()

        with (
            patch("ring.authz.enforcer.build_stateless_enforcer") as full_mock,
            patch(
                "ring.authz.authz.build_stateless_enforcer_for_resources",
            ) as scoped_mock,
        ):
            result = filter_to_authorized(db_session, user, Action.READ, [])

        assert result == []
        full_mock.assert_not_called()
        scoped_mock.assert_not_called()

    def test_empty_bulk_can_skips_loaders(self, db_session: Session) -> None:
        user = UserFactory.create()
        db_session.commit()

        with (
            patch("ring.authz.enforcer.build_stateless_enforcer") as full_mock,
            patch(
                "ring.authz.authz.build_stateless_enforcer_for_resources",
            ) as scoped_mock,
        ):
            result = bulk_can_or_inaccessible(
                db_session, user, Action.READ, []
            )

        assert result == []
        full_mock.assert_not_called()
        scoped_mock.assert_not_called()
