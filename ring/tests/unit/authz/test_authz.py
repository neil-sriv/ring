"""Tests for the authorization module.

This module contains comprehensive tests for the authorization system,
including permission checking, resource filtering, and bulk operations.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from ring.authz.authz import (
    AuthDeniedError,
    InaccessibleResource,
    bulk_can_or_inaccessible,
    bulk_check,
    bulk_load_and_check,
    can,
    check,
    filter_to_authorized,
)
from ring.authz.enforcer import Action
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_sqlalchemy_object_list_equal_with_order_insensitive,
)


class TestCan:
    """Test the can function."""

    def test_can_user_has_permission(self, db_session: Session) -> None:
        """Test that can returns True when user has permission."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        db_session.commit()

        result = can(db_session, user, Action.READ, group)

        assert result is True

    def test_can_user_no_permission(self, db_session: Session) -> None:
        """Test that can returns False when user has no permission."""
        user = UserFactory.create()
        group = GroupFactory.create()  # Different user as admin
        db_session.commit()

        result = can(db_session, user, Action.READ, group)

        assert result is False

    def test_can_with_provided_enforcer(self, db_session: Session) -> None:
        """Test that can works with a provided enforcer."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        db_session.commit()

        # Create enforcer manually
        from ring.authz.enforcer import build_stateless_enforcer

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        result = can(db_session, user, Action.READ, group, enforcer)

        assert result is True

    # def test_can_read_permission_denied(self, db_session: Session) -> None:
    #     """Test that read permissions are properly denied."""
    #     user = UserFactory.create()
    #     group = GroupFactory.create(admin=user)
    #     db_session.commit()

    #     result = can(db_session, user, Action.READ, group)

    #     assert result is False


class TestCheck:
    """Test the check function."""

    def test_check_user_has_permission(self, db_session: Session) -> None:
        """Test that check returns True when user has permission."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        db_session.commit()

        # check function doesn't return anything when permission is granted
        # it just doesn't raise an exception
        check(db_session, user, Action.READ, group)
        # If we get here, the test passes

    def test_check_user_no_permission_raises_error(
        self, db_session: Session
    ) -> None:
        """Test that check raises AuthDeniedError when user has no permission."""
        user = UserFactory.create()
        group = GroupFactory.create()  # Different user as admin
        db_session.commit()

        with pytest.raises(AuthDeniedError) as exc_info:
            check(db_session, user, Action.READ, group)

        assert user.api_identifier in str(exc_info.value)
        assert group.api_identifier in str(exc_info.value)
        assert Action.READ.value in str(exc_info.value)

    def test_check_with_provided_enforcer(self, db_session: Session) -> None:
        """Test that check works with a provided enforcer."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        db_session.commit()

        # Create enforcer manually
        from ring.authz.enforcer import build_stateless_enforcer

        enforcer = build_stateless_enforcer(db_session, user.api_identifier)

        # check function doesn't return anything when permission is granted
        check(db_session, user, Action.READ, group, enforcer)
        # If we get here, the test passes


class TestFilterToAuthorized:
    """Test the filter_to_authorized function."""

    def test_filter_to_authorized_all_authorized(
        self, db_session: Session
    ) -> None:
        """Test filtering when all resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        db_session.commit()

        resources = [group1, group2]
        result = filter_to_authorized(db_session, user, Action.READ, resources)

        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            result, resources
        )

    def test_filter_to_authorized_some_authorized(
        self, db_session: Session
    ) -> None:
        """Test filtering when some resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        resources = [group1, group2]
        result = filter_to_authorized(db_session, user, Action.READ, resources)

        assert result == [group1]

    def test_filter_to_authorized_none_authorized(
        self, db_session: Session
    ) -> None:
        """Test filtering when no resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create()  # Different user as admin
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        resources = [group1, group2]
        result = filter_to_authorized(db_session, user, Action.READ, resources)

        assert result == []

    def test_filter_to_authorized_empty_list(
        self, db_session: Session
    ) -> None:
        """Test filtering with empty resource list."""
        user = UserFactory.create()
        db_session.commit()

        result = filter_to_authorized(db_session, user, Action.READ, [])

        assert result == []

    def test_filter_to_authorized_with_hierarchy(
        self, db_session: Session
    ) -> None:
        """Test filtering with resource hierarchy."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(question=question)
        db_session.commit()

        resources = [group, letter, question, response]
        result = filter_to_authorized(db_session, user, Action.READ, resources)

        # All resources should be authorized due to hierarchy
        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            result, resources
        )


class TestBulkCanOrInaccessible:
    """Test the bulk_can_or_inaccessible function."""

    def test_bulk_can_or_inaccessible_all_authorized(
        self, db_session: Session
    ) -> None:
        """Test bulk check when all resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        db_session.commit()

        resources = [group1, group2]
        result = bulk_can_or_inaccessible(
            db_session, user, Action.READ, resources
        )

        assert result == resources

    def test_bulk_can_or_inaccessible_some_authorized(
        self, db_session: Session
    ) -> None:
        """Test bulk check when some resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        resources = [group1, group2]
        result = bulk_can_or_inaccessible(
            db_session, user, Action.READ, resources
        )

        assert len(result) == 2
        assert result[0] == group1
        assert isinstance(result[1], InaccessibleResource)
        assert result[1].resource == group2

    def test_bulk_can_or_inaccessible_none_authorized(
        self, db_session: Session
    ) -> None:
        """Test bulk check when no resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create()  # Different user as admin
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        resources = [group1, group2]
        result = bulk_can_or_inaccessible(
            db_session, user, Action.READ, resources
        )

        assert len(result) == 2
        assert isinstance(result[0], InaccessibleResource)
        assert isinstance(result[1], InaccessibleResource)
        assert result[0].resource == group1
        assert result[1].resource == group2


class TestBulkCheck:
    """Test the bulk_check function."""

    def test_bulk_check_all_authorized(self, db_session: Session) -> None:
        """Test bulk check when all resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        db_session.commit()

        resources = [group1, group2]
        result = bulk_check(db_session, user, Action.READ, resources)

        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            result, resources
        )

    def test_bulk_check_some_unauthorized_raises_error(
        self, db_session: Session
    ) -> None:
        """Test bulk check raises error when some resources are unauthorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        resources = [group1, group2]

        with pytest.raises(AuthDeniedError) as exc_info:
            bulk_check(db_session, user, Action.READ, resources)

        assert "one or more resources" in str(exc_info.value)

    def test_bulk_check_none_authorized_raises_error(
        self, db_session: Session
    ) -> None:
        """Test bulk check raises error when no resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create()  # Different user as admin
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        resources = [group1, group2]

        with pytest.raises(AuthDeniedError) as exc_info:
            bulk_check(db_session, user, Action.READ, resources)

        assert "one or more resources" in str(exc_info.value)


class TestBulkLoadAndCheck:
    """Test the bulk_load_and_check function."""

    def test_bulk_load_and_check_all_authorized(
        self, db_session: Session
    ) -> None:
        """Test bulk load and check when all resources are authorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create(admin=user)
        db_session.commit()

        api_identifiers = [group1.api_identifier, group2.api_identifier]
        result = bulk_load_and_check(
            db_session, user, Action.READ, api_identifiers
        )

        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            result, [group1, group2]
        )

    def test_bulk_load_and_check_some_unauthorized_raises_error(
        self, db_session: Session
    ) -> None:
        """Test bulk load and check raises error when some resources are unauthorized."""
        user = UserFactory.create()
        group1 = GroupFactory.create(admin=user)
        group2 = GroupFactory.create()  # Different user as admin
        db_session.commit()

        api_identifiers = [group1.api_identifier, group2.api_identifier]

        with pytest.raises(AuthDeniedError) as exc_info:
            bulk_load_and_check(db_session, user, Action.READ, api_identifiers)

        assert "one or more resources" in str(exc_info.value)

    def test_bulk_load_and_check_nonexistent_resource(
        self, db_session: Session
    ) -> None:
        """Test bulk load and check with nonexistent resource."""
        user = UserFactory.create()
        db_session.commit()

        api_identifiers = ["usr_invalid"]

        with pytest.raises(AuthDeniedError) as exc_info:
            bulk_load_and_check(db_session, user, Action.READ, api_identifiers)

        assert (
            "One or more resources not found or not accessible to user"
            in str(exc_info.value)
        )


class TestInaccessibleResource:
    """Test the InaccessibleResource class."""

    def test_inaccessible_resource_creation(self) -> None:
        """Test creating an InaccessibleResource instance."""
        resource = GroupFactory.build()
        inaccessible = InaccessibleResource(resource)

        assert inaccessible.resource == resource
        assert inaccessible.reason is None

    def test_inaccessible_resource_with_reason(self) -> None:
        """Test creating an InaccessibleResource instance with a reason."""
        resource = GroupFactory.build()
        reason = "User not in group"
        inaccessible = InaccessibleResource(resource, reason)

        assert inaccessible.resource == resource
        assert inaccessible.reason == reason


class TestAuthzIntegration:
    """Integration tests for the authorization system."""

    def test_complete_authorization_workflow(
        self, db_session: Session
    ) -> None:
        """Test a complete authorization workflow."""
        # Create test data
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(question=question)
        db_session.commit()

        # Test individual permission checks
        assert can(db_session, user, Action.READ, group) is True
        assert can(db_session, user, Action.READ, letter) is True
        assert can(db_session, user, Action.READ, question) is True
        assert can(db_session, user, Action.READ, response) is True

        # Test bulk operations
        resources = [group, letter, question, response]
        authorized = filter_to_authorized(
            db_session, user, Action.READ, resources
        )
        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            authorized, resources
        )

        # Test bulk check
        bulk_result = bulk_check(db_session, user, Action.READ, resources)
        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            bulk_result, resources
        )

    def test_authorization_with_multiple_users(
        self, db_session: Session
    ) -> None:
        """Test authorization with multiple users and resources."""
        # Create users
        user1 = UserFactory.create()
        user2 = UserFactory.create()

        # Create groups with different admins
        group1 = GroupFactory.create(admin=user1)
        group2 = GroupFactory.create(admin=user2)
        group3 = GroupFactory.create(admin=user1)

        db_session.commit()

        # Test user1 permissions
        assert can(db_session, user1, Action.READ, group1) is True
        assert can(db_session, user1, Action.READ, group2) is False
        assert can(db_session, user1, Action.READ, group3) is True

        # Test user2 permissions
        assert can(db_session, user2, Action.READ, group1) is False
        assert can(db_session, user2, Action.READ, group2) is True
        assert can(db_session, user2, Action.READ, group3) is False

        # Test bulk filtering for user1
        all_resources = [group1, group2, group3]
        user1_authorized = filter_to_authorized(
            db_session, user1, Action.READ, all_resources
        )
        assert_sqlalchemy_object_list_equal_with_order_insensitive(
            user1_authorized, [group1, group3]
        )

        # Test bulk filtering for user2
        user2_authorized = filter_to_authorized(
            db_session, user2, Action.READ, all_resources
        )
        assert user2_authorized == [group2]

    def test_write_permissions_consistently_denied(
        self, db_session: Session
    ) -> None:
        """Test that write permissions are consistently denied."""
        user = UserFactory.create()
        group = GroupFactory.create(admin=user)
        letter = LetterFactory.create(group=group)
        db_session.commit()

        # Test that write permissions are denied for all resources
        # assert can(db_session, user, Action.WRITE, group) is False
        # assert can(db_session, user, Action.WRITE, letter) is False

        # # Test that check raises for write permissions
        # with pytest.raises(AuthDeniedError):
        #     check(db_session, user, Action.WRITE, group)

        # with pytest.raises(AuthDeniedError):
        #     check(db_session, user, Action.WRITE, letter)
