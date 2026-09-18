"""Characterization tests for Casbin enforcer loading and allow/deny outcomes.

These tests freeze current auth semantics so later refactors of
``build_stateless_enforcer`` (cartesian-join fix, candidate-scoped filter)
can prove decisions are unchanged. Prefer enforce/filter outcomes over exact
duplicate-preserving policy lists; where policy sets are checked, use unique
order-insensitive ``(child, parent)`` / policy triples.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session

from ring.authz.authz import can, filter_to_authorized
from ring.authz.enforcer import (
    Action,
    build_stateless_enforcer,
    enforce_stateless,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_sqlalchemy_object_list_equal_with_order_insensitive,
)


def _unique_pairs(policies: list[list[str]]) -> set[tuple[str, str]]:
    return {(row[0], row[1]) for row in policies}


def _unique_policy_triples(
    policies: list[list[str]],
) -> set[tuple[str, str, str]]:
    return {(row[0], row[1], row[2]) for row in policies}


@pytest.fixture
def hierarchy_fixture(db_session: Session) -> dict[str, Any]:
    """User in group A with letter→question→response; outsider group B."""
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


class TestEnforcerPolicySets:
    """Document today's unique g / g2 / p sets (order-insensitive)."""

    def test_unique_policy_sets_for_hierarchy(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]
        other_member = hierarchy_fixture["other_member"]
        group_a = hierarchy_fixture["group_a"]
        letter_a = hierarchy_fixture["letter_a"]
        question_a = hierarchy_fixture["question_a"]
        response_a = hierarchy_fixture["response_a"]

        enforcer = build_stateless_enforcer(db_session, member.api_identifier)

        # g lists every member of groups that contain the subject (join shape).
        assert _unique_pairs(enforcer.get_grouping_policy()) == {
            (member.api_identifier, group_a.api_identifier),
            (other_member.api_identifier, group_a.api_identifier),
        }
        assert _unique_policy_triples(enforcer.get_policy()) == {
            (
                group_a.api_identifier,
                group_a.api_identifier,
                Action.READ.value,
            ),
            (
                member.api_identifier,
                member.api_identifier,
                Action.READ.value,
            ),
            (
                member.api_identifier,
                member.api_identifier,
                Action.WRITE.value,
            ),
        }
        assert _unique_pairs(enforcer.get_named_grouping_policy("g2")) == {
            (member.api_identifier, group_a.api_identifier),
            (other_member.api_identifier, group_a.api_identifier),
            (letter_a.api_identifier, group_a.api_identifier),
            (question_a.api_identifier, letter_a.api_identifier),
            (response_a.api_identifier, question_a.api_identifier),
        }

    def test_unique_policy_sets_multi_group(self, db_session: Session) -> None:
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        letter1 = LetterFactory.create(group=group1)
        letter2 = LetterFactory.create(group=group2)
        db_session.commit()

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        assert _unique_pairs(enforcer.get_grouping_policy()) == {
            (user.api_identifier, group1.api_identifier),
            (user.api_identifier, group2.api_identifier),
        }
        assert _unique_policy_triples(enforcer.get_policy()) == {
            (
                group1.api_identifier,
                group1.api_identifier,
                Action.READ.value,
            ),
            (
                group2.api_identifier,
                group2.api_identifier,
                Action.READ.value,
            ),
            (
                user.api_identifier,
                user.api_identifier,
                Action.READ.value,
            ),
            (
                user.api_identifier,
                user.api_identifier,
                Action.WRITE.value,
            ),
        }
        assert _unique_pairs(enforcer.get_named_grouping_policy("g2")) == {
            (user.api_identifier, group1.api_identifier),
            (user.api_identifier, group2.api_identifier),
            (letter1.api_identifier, group1.api_identifier),
            (letter2.api_identifier, group2.api_identifier),
        }


class TestAllowDenyMatrix:
    """Lock READ allow/deny for in-group hierarchy and outsider denial."""

    def test_member_can_read_in_group_hierarchy(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]
        other_member = hierarchy_fixture["other_member"]
        in_group = [
            hierarchy_fixture["group_a"],
            hierarchy_fixture["letter_a"],
            hierarchy_fixture["question_a"],
            hierarchy_fixture["response_a"],
            other_member,
        ]

        enforcer = build_stateless_enforcer(db_session, member.api_identifier)

        for resource in in_group:
            assert (
                enforce_stateless(
                    db_session,
                    member.api_identifier,
                    resource.api_identifier,
                    Action.READ,
                    enforcer,
                )
                is True
            )
            assert (
                can(db_session, member, Action.READ, resource, enforcer)
                is True
            )

    def test_outsider_cannot_read_group_a(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        outsider = hierarchy_fixture["outsider"]
        denied = [
            hierarchy_fixture["group_a"],
            hierarchy_fixture["letter_a"],
            hierarchy_fixture["question_a"],
            hierarchy_fixture["response_a"],
            hierarchy_fixture["member"],
            hierarchy_fixture["other_member"],
        ]

        enforcer = build_stateless_enforcer(
            db_session, outsider.api_identifier
        )

        for resource in denied:
            assert (
                enforce_stateless(
                    db_session,
                    outsider.api_identifier,
                    resource.api_identifier,
                    Action.READ,
                    enforcer,
                )
                is False
            )
            assert (
                can(db_session, outsider, Action.READ, resource, enforcer)
                is False
            )

    def test_member_cannot_read_group_b(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]
        denied = [
            hierarchy_fixture["group_b"],
            hierarchy_fixture["letter_b"],
            hierarchy_fixture["question_b"],
            hierarchy_fixture["response_b"],
            hierarchy_fixture["outsider"],
        ]

        enforcer = build_stateless_enforcer(db_session, member.api_identifier)

        for resource in denied:
            assert (
                can(db_session, member, Action.READ, resource, enforcer)
                is False
            )

    def test_write_denied_as_today(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        """WRITE remains denied for members (current policy only grants READ)."""
        member = hierarchy_fixture["member"]
        resources = [
            hierarchy_fixture["group_a"],
            hierarchy_fixture["letter_a"],
            hierarchy_fixture["question_a"],
            hierarchy_fixture["response_a"],
        ]

        enforcer = build_stateless_enforcer(db_session, member.api_identifier)

        for resource in resources:
            assert (
                enforce_stateless(
                    db_session,
                    member.api_identifier,
                    resource.api_identifier,
                    Action.WRITE,
                    enforcer,
                )
                is False
            )
            assert (
                can(db_session, member, Action.WRITE, resource, enforcer)
                is False
            )


class TestFilterToAuthorizedCharacterization:
    """filter_to_authorized outcomes for mixed lists and empty input."""

    def test_filter_mixed_in_and_out_of_group(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]
        allowed = [
            hierarchy_fixture["group_a"],
            hierarchy_fixture["letter_a"],
            hierarchy_fixture["question_a"],
            hierarchy_fixture["response_a"],
            hierarchy_fixture["other_member"],
        ]
        denied = [
            hierarchy_fixture["group_b"],
            hierarchy_fixture["letter_b"],
            hierarchy_fixture["question_b"],
            hierarchy_fixture["response_b"],
            hierarchy_fixture["outsider"],
        ]
        mixed = allowed + denied

        result = filter_to_authorized(db_session, member, Action.READ, mixed)

        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            list(result), allowed
        )

    def test_filter_empty_list_returns_empty(
        self, db_session: Session, hierarchy_fixture: dict[str, Any]
    ) -> None:
        member = hierarchy_fixture["member"]

        result = filter_to_authorized(db_session, member, Action.READ, [])

        assert result == []

    def test_filter_multi_group_membership(self, db_session: Session) -> None:
        user = UserFactory.create()
        outsider = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        letter1 = LetterFactory.create(group=group1)
        letter2 = LetterFactory.create(group=group2)
        other_group = GroupFactory.create(admin=outsider)
        other_letter = LetterFactory.create(group=other_group)
        db_session.commit()

        result = filter_to_authorized(
            db_session,
            user,
            Action.READ,
            [group1, group2, letter1, letter2, other_group, other_letter],
        )

        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            list(result), [group1, group2, letter1, letter2]
        )
