"""Tests for the group API endpoints.

This module contains tests for all group-related API endpoints, including
group creation, member management, and group settings. It verifies both
successful operations and error cases.
"""

from __future__ import annotations

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import GroupSummary
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_api_model_not_found,
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)


class TestGroupApi:
    """Test suite for group API endpoints.

    This class contains tests for all group-related API operations,
    including CRUD operations and member management.
    """

    def test_create_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test creating a new group with valid data.

        This test verifies that:
        1. A group can be created with a valid name and admin
        2. The response contains the correct group data
        3. The group is properly stored in the database

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        input = {
            "name": "Test Group",
            "admin_api_identifier": current_user.api_identifier,
        }
        response = authenticated_client.post(
            "/parties/group",
            json=input,
        )

        assert response.status_code == 201
        data = response.json()
        assert data == data | {
            "name": "Test Group",
            "admin": data["admin"]
            | {
                "api_identifier": current_user.api_identifier,
            },
            "members": [
                data["admin"]
                | {
                    "api_identifier": current_user.api_identifier,
                }
            ],
        }

        db_group = db_session.scalar(
            sqlalchemy.select(Group).filter(Group.name == "Test Group")
        )
        assert db_group
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            db_group,
            data,
        )

    def test_create_group_invalid_admin(
        self,
        authenticated_client: TestClient,
    ):
        """Test creating a group with an invalid admin.

        This test verifies that:
        1. Creating a group with a non-existent admin fails
        2. The response contains the correct error message

        Args:
            authenticated_client (TestClient): Authenticated test client
        """
        input = {
            "name": "Test Group",
            "admin_api_identifier": "invalid-user",
        }
        response = authenticated_client.post(
            "/parties/group",
            json=input,
        )

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, User, ["invalid-user"])

    def test_list_groups(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test listing groups for a user.

        This test verifies that:
        1. Groups where the user is admin are included
        2. Groups where the user is a member are included
        3. Other groups are not included
        4. The response contains the correct group data

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        admin_groups = [
            GroupFactory.create(admin=current_user) for _ in range(5)
        ]
        member_groups = [GroupFactory.create() for _ in range(5)]
        for group in member_groups:
            group.members.append(current_user)
        [GroupFactory.create() for _ in range(5)]
        db_session.commit()

        response = authenticated_client.get(
            f"/parties/groups/?user_api_id={current_user.api_identifier}"
        )

        assert response.status_code == 200
        data = response.json()

        assert_pydantic_models_json_dump_in_response_dict(
            admin_groups + member_groups,
            data,
            override_pydantic_model=GroupSummary,
        )

    def test_read_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test reading a group that the user is a member of.

        This test verifies that:
        1. A group can be read by its members
        2. The response contains the correct group data
        3. The response matches the database state

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        group = GroupFactory.create()
        group.members.append(current_user)
        db_session.commit()

        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}"
        )

        assert response.status_code == 200
        data = response.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            group,
            data,
        )

    def test_read_group_not_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ):
        """Test reading a group that the user is not a member of.

        This test verifies that:
        1. Non-members cannot read the group
        2. The response contains the correct error message
        3. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}"
        )

        assert response.status_code == 404
        data = response.json()
        assert data == {"detail": "Group not found"}

    def test_read_group_not_found(
        self,
        authenticated_client: TestClient,
    ):
        """Test reading a non-existent group.

        This test verifies that:
        1. Reading a non-existent group fails
        2. The response contains the correct error message
        3. The response indicates the group was not found

        Args:
            authenticated_client (TestClient): Authenticated test client
        """
        response = authenticated_client.get(f"/parties/group/invalid-group")

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Group, ["invalid-group"])

    def test_add_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ):
        """Test adding a member to a group.

        This test verifies that:
        1. A user can be added as a member
        2. The response contains the updated group data
        3. The user is actually added to the group
        4. The database state is updated correctly

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        db_session.commit()

        user = UserFactory.create()
        db_session.commit()

        assert user not in group.members

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/{user.api_identifier}"
        )

        assert response.status_code == 200
        data = response.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            group,
            data,
        )
        assert user in group.members

    def test_add_member_duplicate(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ):
        """Test adding a member who is already in the group.

        This test verifies that:
        1. Adding an existing member succeeds
        2. The response contains the correct group data
        3. The member remains in the group
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        user = UserFactory.create()
        group.members.append(user)
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/{user.api_identifier}"
        )

        assert response.status_code == 200
        data = response.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            group,
            data,
        )
        assert user in group.members

    def test_add_member_not_found(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ):
        """Test adding a non-existent member to a group.

        This test verifies that:
        1. Adding a non-existent user fails
        2. Adding to a non-existent group fails
        3. The response contains the correct error message
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/invalid-user"
        )

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, User, ["invalid-user"])

        response = authenticated_client.post(
            f"/parties/group/invalid-group:add_member/invalid-user"
        )

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Group, ["invalid-group"])

    def test_remove_member(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test removing a member from a group.

        This test verifies that:
        1. A member can be removed from the group
        2. The response contains the updated group data
        3. The user is actually removed from the group
        4. The database state is updated correctly

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        user = UserFactory.create()
        group.members.append(user)
        db_session.commit()

        assert user in group.members

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:remove_member/{user.api_identifier}"
        )

        assert response.status_code == 200
        data = response.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            group,
            data,
        )
        assert user not in group.members

    def test_remove_member_not_found(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test removing a non-existent member from a group.

        This test verifies that:
        1. Removing a non-existent user fails
        2. Removing from a non-existent group fails
        3. The response contains the correct error message
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:remove_member/invalid-user"
        )

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, User, ["invalid-user"])

        response = authenticated_client.post(
            f"/parties/group/invalid-group:remove_member/invalid-user"
        )

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Group, ["invalid-group"])

    def test_remove_member_not_member(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test removing a user who is not a member of the group.

        This test verifies that:
        1. Removing a non-member fails
        2. The response contains the correct error message
        3. The database state remains unchanged
        4. The user remains not in the group

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        user = UserFactory.create()
        db_session.commit()

        assert user not in group.members

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:remove_member/{user.api_identifier}"
        )

        assert response.status_code == 400
        data = response.json()
        assert data == {"detail": "User is not a member of the group"}

    def test_update_group_cycle_length(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test updating a group's cycle length.

        This test verifies that:
        1. The cycle length can be updated by the admin
        2. The response contains the updated group data
        3. The new cycle length is stored correctly
        4. The database state is updated

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        group = GroupFactory.create(admin=current_user)
        db_session.commit()

        # Test updating cycle length
        response = authenticated_client.patch(
            f"/parties/group/{group.api_identifier}",
            json={"cycle_length": 60},
        )

        assert response.status_code == 200
        data = response.json()
        assert_pydantic_model_json_dump_equivalent_to_response_dict(
            group,
            data,
        )
        assert group.cycle_length == 60

    def test_update_group_cycle_length_invalid(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test updating a group's cycle length with invalid values.

        This test verifies that:
        1. Setting cycle length to 0 fails
        2. Setting cycle length to negative fails
        3. The response contains the correct error message
        4. The original cycle length remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        group = GroupFactory.create(admin=current_user)
        db_session.commit()
        original_cycle_length = group.cycle_length

        # Test updating with invalid cycle length
        response = authenticated_client.patch(
            f"/parties/group/{group.api_identifier}",
            json={"cycle_length": 0},
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Cycle length must be greater than 0"
        }
        assert group.cycle_length == original_cycle_length

        # Test updating with negative cycle length
        response = authenticated_client.patch(
            f"/parties/group/{group.api_identifier}",
            json={"cycle_length": -1},
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Cycle length must be greater than 0"
        }
        assert group.cycle_length == original_cycle_length

    def test_update_group_cycle_length_not_admin(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test updating a group's cycle length when not the admin.

        This test verifies that:
        1. Non-admin users cannot update cycle length
        2. The response contains the correct error message
        3. The cycle length remains unchanged
        4. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        other_admin = UserFactory.create()
        group = GroupFactory.create(admin=other_admin)
        group.members.append(current_user)
        db_session.commit()
        original_cycle_length = group.cycle_length

        response = authenticated_client.patch(
            f"/parties/group/{group.api_identifier}",
            json={"cycle_length": 60},
        )

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Only the group admin can update the group information"
        }
        assert group.cycle_length == original_cycle_length
