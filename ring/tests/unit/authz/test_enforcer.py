"""Tests for the authorization enforcer module.

This module contains comprehensive tests for the authorization enforcer,
including stateless enforcer building, permission enforcement, and
various authorization scenarios.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from casbin import Enforcer
from sqlalchemy.orm import Session

from ring.authz.enforcer import (
    Action,
    build_stateless_enforcer,
    enforce_stateless,
    get_enforcer,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import assert_lists_equal_with_order_insensitive


class TestAction:
    """Test the Action enum."""

    def test_action_values(self) -> None:
        """Test that Action enum has correct values."""
        assert Action.READ.value == "read"
        assert Action.WRITE.value == "write"


class TestBuildStatelessEnforcer:
    """Test the build_stateless_enforcer function."""

    def test_build_stateless_enforcer_no_user_groups(
        self, db_session: Session
    ) -> None:
        """Test building enforcer for user with no groups."""

        user = UserFactory.create()
        db_session.commit()

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        assert enforcer.get_policy() == []
        assert enforcer.get_grouping_policy() == []
        assert enforcer.get_named_grouping_policy("g2") == []

    def test_build_stateless_enforcer_with_user_groups(
        self, db_session: Session
    ) -> None:
        """Test building enforcer for user with groups."""

        # Create user and group
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        db_session.commit()

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        assert_lists_equal_with_order_insensitive(
            enforcer.get_policy(),
            [[group.api_identifier, group.api_identifier, Action.READ.value]],
        )
        assert_lists_equal_with_order_insensitive(
            enforcer.get_grouping_policy(),
            [[user.api_identifier, group.api_identifier]],
        )
        assert_lists_equal_with_order_insensitive(
            enforcer.get_named_grouping_policy("g2"),
            [[user.api_identifier, group.api_identifier]],
        )

    def test_build_stateless_enforcer_with_resource_hierarchy(
        self, db_session: Session
    ) -> None:
        """Test building enforcer with complete resource hierarchy."""

        # Create complete hierarchy: user -> group -> letter -> question -> response
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(question=question)
        db_session.commit()

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        assert_lists_equal_with_order_insensitive(
            enforcer.get_policy(),
            [[group.api_identifier, group.api_identifier, Action.READ.value]],
        )

        # Check g1 policies (user-group relationships)
        assert_lists_equal_with_order_insensitive(
            enforcer.get_grouping_policy(),
            [[user.api_identifier, group.api_identifier]],
        )

        # Check g2 policies (resource hierarchy)
        assert_lists_equal_with_order_insensitive(
            enforcer.get_named_grouping_policy("g2"),
            [
                [user.api_identifier, group.api_identifier],
                [letter.api_identifier, group.api_identifier],
                [question.api_identifier, letter.api_identifier],
                [response.api_identifier, question.api_identifier],
            ],
        )

        # Check p policies (permissions)
        assert_lists_equal_with_order_insensitive(
            enforcer.get_policy(),
            [[group.api_identifier, group.api_identifier, Action.READ.value]],
        )

    def test_build_stateless_enforcer_multiple_groups(
        self, db_session: Session
    ) -> None:
        """Test building enforcer for user with multiple groups."""

        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        db_session.commit()

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        assert_lists_equal_with_order_insensitive(
            enforcer.get_policy(),
            [
                [
                    group1.api_identifier,
                    group1.api_identifier,
                    Action.READ.value,
                ],
                [
                    group2.api_identifier,
                    group2.api_identifier,
                    Action.READ.value,
                ],
            ],
        )
        assert_lists_equal_with_order_insensitive(
            enforcer.get_grouping_policy(),
            [
                [user.api_identifier, group1.api_identifier],
                [user.api_identifier, group2.api_identifier],
            ],
        )
        assert_lists_equal_with_order_insensitive(
            enforcer.get_named_grouping_policy("g2"),
            [
                [user.api_identifier, group1.api_identifier],
                [user.api_identifier, group2.api_identifier],
            ],
        )

    def test_build_stateless_enforcer_nonexistent_user(
        self, db_session: Session
    ) -> None:
        """Test building enforcer for non-existent user."""

        enforcer = build_stateless_enforcer(db_session, "nonexistent_user_id")

        assert enforcer.get_policy() == []
        assert enforcer.get_grouping_policy() == []
        assert enforcer.get_named_grouping_policy("g2") == []


class TestEnforceStateless:
    """Test the enforce_stateless function."""

    def test_enforce_stateless_without_enforcer(
        self, db_session: Session
    ) -> None:
        """Test enforce_stateless when no enforcer is provided."""
        group = GroupFactory.create()
        db_session.commit()

        result = enforce_stateless(
            db_session,
            group.admin.api_identifier,
            group.api_identifier,
            Action.READ,
        )

        assert result is True

    def test_enforce_stateless_with_provided_enforcer(
        self, db_session: Session
    ) -> None:
        """Test enforce_stateless when enforcer is provided."""

        group = GroupFactory.create()
        db_session.commit()
        enforcer = build_stateless_enforcer(
            db_session, group.admin.api_identifier
        )

        result = enforce_stateless(
            db_session,
            group.admin.api_identifier,
            group.api_identifier,
            Action.WRITE,
            enforcer,
        )

        assert result is False

    def test_enforce_stateless_denies_access(
        self, db_session: Session
    ) -> None:
        """Test enforce_stateless when access is denied."""

        result = enforce_stateless(
            db_session, "user_id", "resource_id", Action.READ
        )

        assert result is False


class TestEnforcerIntegration:
    """Integration tests for the enforcer system."""

    def test_complete_authorization_flow(self, db_session: Session) -> None:
        """Test complete authorization flow with real data."""

        # Create test data
        user = UserFactory.create()
        group = GroupFactory.create()
        letter = LetterFactory.create(group=group)
        group.members.append(user)
        db_session.commit()

        # Test authorization
        result = enforce_stateless(
            db_session, user.api_identifier, letter.api_identifier, Action.READ
        )

        # Verify the enforcer was called correctly
        assert result is True

    def test_action_enum_comparison(self) -> None:
        """Test that Action enum values can be compared correctly."""
        assert Action.READ == Action.READ
        assert Action.READ != Action.WRITE
        assert Action.READ.value == "read"
        assert Action.WRITE.value == "write"

    def test_action_enum_string_conversion(self) -> None:
        """Test that Action enum converts to string correctly."""
        assert str(Action.READ) == "Action.READ"
        assert repr(Action.WRITE) == "<Action.WRITE: 'write'>"
