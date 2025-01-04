import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_api_model_not_found,
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)


class TestGroupApi:
    def test_create_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
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
        )

    def test_read_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
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
        response = authenticated_client.get(f"/parties/group/invalid-group")

        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Group, ["invalid-group"])

    def test_add_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ):
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
