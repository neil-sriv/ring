"""API dual-write / dual-read: flags off by default; fake when on."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.auth.dual_sync.metrics import metrics
from ring.auth.dual_sync.service import LocalIdentity, run_identity_upsert
from ring.auth.idp_client.factory import set_identity_client_override
from ring.fastapp.config import get_config
from ring.parties.models.user_model import User
from ring.tests.factories.parties.invite_factory import InviteFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.conftest import TClientForUser
from ring.vendor.genesis_idp import (
    FakeIdentityClient,
    IdentityUpsert,
    format_created_at,
)

HASH = "$2b$12$" + ("a" * 53)


@pytest.fixture
def fake_identity() -> FakeIdentityClient:
    fake = FakeIdentityClient()
    set_identity_client_override(fake)
    metrics.reset()
    yield fake
    set_identity_client_override(None)
    metrics.reset()


def _enable_dual(
    monkeypatch: pytest.MonkeyPatch,
    *,
    write: bool = False,
    read: bool = False,
) -> None:
    config = get_config()
    monkeypatch.setattr(config, "AUTH_DUAL_WRITE", write)
    monkeypatch.setattr(config, "AUTH_DUAL_READ", read)


def test_flags_default_off() -> None:
    config = get_config()
    assert config.AUTH_DUAL_WRITE is False
    assert config.AUTH_DUAL_READ is False
    assert config.IDENTITY_SERVICE_BASE_URL == ""
    assert config.IDP_DIRECTORY_API_TOKEN == ""


def test_create_user_does_not_dual_write_when_flag_off(
    unauthenticated_client: TestClient,
    faker,
    fake_identity: FakeIdentityClient,
) -> None:
    email, name, password = faker.email(), faker.name(), faker.password()
    response = unauthenticated_client.post(
        "/parties/user",
        json={"email": email, "name": name, "password": password},
    )
    assert response.status_code == 201
    assert fake_identity.upsert_calls == []


def test_create_user_dual_writes_api_identifier_not_pk(
    unauthenticated_client: TestClient,
    faker,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, write=True)
    email, name, password = faker.email(), faker.name(), faker.password()
    response = unauthenticated_client.post(
        "/parties/user",
        json={"email": email, "name": name, "password": password},
    )
    assert response.status_code == 201
    body = response.json()
    user = db_session.query(User).filter(User.email == email).one()
    assert len(fake_identity.upsert_calls) == 1
    payload = fake_identity.upsert_calls[0]
    assert payload.external_id == body["api_identifier"]
    assert payload.external_id.startswith("usr_")
    assert payload.external_id != str(user.id)
    assert payload.hashed_password == user.hashed_password
    assert payload.hashed_password.startswith("$")
    assert payload.hashed_password != password
    assert payload.created_at
    assert metrics.snapshot().write_successes == 1


def test_dual_write_failure_does_not_fail_signup(
    unauthenticated_client: TestClient,
    faker,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, write=True)
    fake_identity.fail_upserts = True
    email, name, password = faker.email(), faker.name(), faker.password()
    response = unauthenticated_client.post(
        "/parties/user",
        json={"email": email, "name": name, "password": password},
    )
    assert response.status_code == 201
    assert metrics.snapshot().write_failures == 1


def test_register_dual_writes(
    unauthenticated_client: TestClient,
    faker,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, write=True)
    invite = InviteFactory.create()
    db_session.commit()
    password = faker.password()
    response = unauthenticated_client.post(
        f"/parties/register/{invite.one_time_token.token}",
        json={
            "email": invite.email,
            "name": faker.name(),
            "password": password,
        },
    )
    assert response.status_code == 200
    assert fake_identity.upsert_calls[0].hashed_password.startswith("$")
    assert fake_identity.upsert_calls[0].hashed_password != password


def test_login_succeeds_and_dual_reads_without_serving_new_path(
    unauthenticated_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, read=True)
    user = UserFactory.create(password="test-password")
    db_session.commit()
    response = unauthenticated_client.post(
        "/login/access-token",
        data={"username": user.email, "password": "test-password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "email" not in body
    assert fake_identity.get_calls == [user.api_identifier]
    assert metrics.snapshot().read_missing == 1

    fake_identity.upsert_identity(
        IdentityUpsert(
            external_id=user.api_identifier,
            email=user.email,
            name=user.name,
            hashed_password=user.hashed_password,
            admin=user.admin,
            created_at=format_created_at(user.created_at),
        )
    )
    remote = fake_identity.get_identity(user.api_identifier)
    assert remote is not None
    assert remote.credential_present is True
    assert not hasattr(remote, "hashed_password")
    metrics.reset()
    again = unauthenticated_client.post(
        "/login/access-token",
        data={"username": user.email, "password": "test-password"},
    )
    assert again.status_code == 200
    assert metrics.snapshot().read_matches == 1


def test_login_still_works_when_dual_read_errors(
    unauthenticated_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, read=True)
    fake_identity.fail_reads = True
    user = UserFactory.create(password="test-password")
    db_session.commit()
    response = unauthenticated_client.post(
        "/login/access-token",
        data={"username": user.email, "password": "test-password"},
    )
    assert response.status_code == 200
    assert metrics.snapshot().read_failures == 1


def test_me_dual_reads(
    get_client_for_user: TClientForUser,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, read=True)
    user = UserFactory.create()
    db_session.commit()
    client = get_client_for_user(user)
    response = client.get("/parties/me")
    assert response.status_code == 200
    assert response.json()["email"] == user.email
    assert fake_identity.get_calls == [user.api_identifier]


def test_update_me_dual_writes(
    authenticated_client: TestClient,
    current_user: User,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, write=True)
    response = authenticated_client.patch(
        "/parties/me",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    payload = fake_identity.upsert_calls[0]
    assert payload.name == "New Name"
    assert payload.external_id == current_user.api_identifier
    assert payload.hashed_password == current_user.hashed_password


def test_password_change_dual_writes_hash_not_plaintext(
    authenticated_client: TestClient,
    current_user: User,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, write=True)
    response = authenticated_client.patch(
        "/parties/me/password",
        json={
            "current_password": "password",
            "new_password": "newer-password",
        },
    )
    assert response.status_code == 200
    payload = fake_identity.upsert_calls[0]
    assert payload.hashed_password.startswith("$")
    assert payload.hashed_password != "newer-password"
    assert payload.hashed_password == current_user.hashed_password


@pytest.mark.admin(True)
def test_admin_edit_dual_writes(
    authenticated_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    fake_identity: FakeIdentityClient,
) -> None:
    _enable_dual(monkeypatch, write=True)
    user = UserFactory.create()
    db_session.commit()
    response = authenticated_client.patch(
        f"/parties/user/{user.api_identifier}",
        json={"name": "Admin Set"},
    )
    assert response.status_code == 200
    assert fake_identity.upsert_calls[0].name == "Admin Set"
    fake_identity.upsert_calls.clear()
    admin_resp = authenticated_client.patch(
        f"/parties/{user.api_identifier}/admin"
    )
    assert admin_resp.status_code == 200
    assert fake_identity.upsert_calls[0].admin is True


def test_stats_requires_admin(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/auth/dual-sync/stats")
    assert response.status_code == 403


@pytest.mark.admin(True)
def test_stats_endpoint_reports_counts(
    authenticated_client: TestClient,
    fake_identity: FakeIdentityClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_dual(monkeypatch, write=True, read=True)
    run_identity_upsert(
        LocalIdentity(
            external_id="usr_statstat",
            email="s@example.com",
            name="S",
            hashed_password=HASH,
            admin=False,
            created_at=datetime.now(UTC),
        )
    )
    response = authenticated_client.get("/auth/dual-sync/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["dual_write_enabled"] is True
    assert body["dual_read_enabled"] is True
    assert body["write_successes"] == 1
    assert body["drift_count"] == 0
    assert body["write_success_rate"] == 1.0
