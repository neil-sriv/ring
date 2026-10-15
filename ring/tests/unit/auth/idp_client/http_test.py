"""HTTP identity client against a mock IdP transport (v2)."""

from __future__ import annotations

import json

import httpx
import pytest

from ring.auth.idp_client.config import IdentityClientConfig
from ring.auth.idp_client.errors import IdentityClientError
from ring.auth.idp_client.http import HttpIdentityClient
from ring.auth.idp_client.models import IdentityPatch, IdentityUpsert
from ring.auth.idp_client.stub import (
    STUB_ACCESS_TOKEN,
    app,
    reset_stub,
    set_credential_store_failures,
)

HASH = "$2b$12$" + ("a" * 53)
CREATED = "2024-01-15T12:00:00Z"
TOKEN = "idp-directory-token-32chars-min"


def _identity_json(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "id": "usr_idp_1",
        "external_id": "usr_abc",
        "email": "a@example.com",
        "name": "A",
        "admin": False,
        "credential_present": True,
        "created_at": CREATED,
        "updated_at": "2026-10-15T02:35:00Z",
    }
    body.update(overrides)
    return body


def _config(**overrides: object) -> IdentityClientConfig:
    values: dict[str, object] = {
        "base_url": "http://id.test",
        "api_token": TOKEN,
        "timeout_seconds": 0.5,
        "write_retries": 3,
    }
    values.update(overrides)
    return IdentityClientConfig(**values)  # type: ignore[arg-type]


def _client(
    handler: httpx.BaseTransport, **config: object
) -> HttpIdentityClient:
    return HttpIdentityClient(_config(**config), transport=handler)


def _upsert() -> IdentityUpsert:
    return IdentityUpsert(
        external_id="usr_abc",
        email="a@example.com",
        name="A",
        hashed_password=HASH,
        admin=False,
        created_at=CREATED,
    )


def test_upsert_and_get_round_trip() -> None:
    store: dict[str, dict[str, object]] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {TOKEN}"
        assert "/oauth/token" not in str(request.url)
        if request.method == "PUT":
            assert request.url.path == "/api/v1/identities/usr_abc"
            body = json.loads(request.content)
            assert body["hashed_password"] == HASH
            assert body["created_at"] == CREATED
            assert "password" not in body
            store[body["external_id"]] = body
            return httpx.Response(201, json=_identity_json())
        if request.url.params.get("email"):
            return httpx.Response(200, json=_identity_json())
        if request.url.path.endswith("usr_missing"):
            return httpx.Response(
                404,
                json={
                    "error": "not_found",
                    "error_description": "identity not found",
                },
            )
        return httpx.Response(200, json=_identity_json())

    client = _client(httpx.MockTransport(handler))
    created = client.upsert_identity(_upsert())
    assert created.external_id == "usr_abc"
    assert created.credential_present is True
    assert "hashed_password" not in created.model_dump()
    fetched = client.get_identity("usr_abc")
    assert fetched is not None
    assert fetched.email == "a@example.com"
    by_email = client.get_identity_by_email("a@example.com")
    assert by_email is not None
    assert client.get_identity("usr_missing") is None
    client.close()


def test_get_rejects_hash_in_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_identity_json(hashed_password=HASH))

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(IdentityClientError, match="hashed_password"):
        client.get_identity("usr_abc")
    client.close()


def test_timeout_becomes_identity_client_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow")

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(IdentityClientError, match="timeout"):
        client.upsert_identity(_upsert())
    client.close()


def test_error_body_is_parsed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "error": "unauthorized",
                "error_description": "bearer token is missing or invalid",
            },
        )

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(IdentityClientError) as exc_info:
        client.get_identity("usr_abc")
    assert exc_info.value.status_code == 401
    assert exc_info.value.error == "unauthorized"
    client.close()


def test_put_retries_credential_store_unavailable() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(
                502,
                json={
                    "error": "credential_store_unavailable",
                    "error_description": "authn down",
                },
            )
        return httpx.Response(200, json=_identity_json())

    client = _client(httpx.MockTransport(handler))
    created = client.upsert_identity(_upsert())
    assert created.credential_present is True
    assert calls["n"] == 2
    client.close()


def test_non_retryable_502_is_not_retried() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            502,
            json={
                "error": "bad_gateway",
                "error_description": "proxy",
            },
        )

    client = _client(httpx.MockTransport(handler), write_retries=3)
    with pytest.raises(IdentityClientError) as exc_info:
        client.upsert_identity(_upsert())
    assert exc_info.value.status_code == 502
    assert calls["n"] == 1
    client.close()


def test_put_gives_up_after_retries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            502,
            json={
                "error": "credential_store_unavailable",
                "error_description": "authn down",
            },
        )

    client = _client(httpx.MockTransport(handler), write_retries=2)
    with pytest.raises(IdentityClientError) as exc_info:
        client.upsert_identity(_upsert())
    assert exc_info.value.status_code == 502
    assert exc_info.value.error == "credential_store_unavailable"
    client.close()


def test_configurable_paths() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.path}")
        return httpx.Response(200, json=_identity_json())

    client = _client(
        httpx.MockTransport(handler),
        identity_path="/v2/people/{external_id}",
        collection_path="/v2/people",
    )
    client.get_identity("usr_abc")
    client.get_identity_by_email("a@example.com")
    assert seen[0] == "GET /v2/people/usr_abc"
    assert seen[1].startswith("GET /v2/people")
    client.close()


def test_create_and_patch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert request.url.path == "/api/v1/identities"
            body = json.loads(request.content)
            assert body["hashed_password"] == HASH
            return httpx.Response(201, json=_identity_json())
        if request.method == "PATCH":
            body = json.loads(request.content)
            assert "hashed_password" not in body
            assert body["name"] is None
            return httpx.Response(
                200, json=_identity_json(name=None, admin=True)
            )
        return httpx.Response(500, json={"error": "unexpected"})

    client = _client(httpx.MockTransport(handler))
    created = client.create_identity(_upsert())
    assert created.external_id == "usr_abc"
    patched = client.patch_identity(
        "usr_abc", IdentityPatch(name=None, admin=True)
    )
    assert patched.admin is True
    client.close()


class _StarletteTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        from starlette.testclient import TestClient

        with TestClient(app) as inner:
            response = inner.request(
                request.method,
                request.url.path
                + (f"?{request.url.query}" if request.url.query else ""),
                headers={
                    key: value
                    for key, value in request.headers.items()
                    if key.lower() != "host"
                },
                content=request.content,
            )
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
        )


def test_http_client_against_local_stub() -> None:
    reset_stub()
    client = HttpIdentityClient(
        IdentityClientConfig(
            base_url="http://id.test",
            api_token=STUB_ACCESS_TOKEN,
        ),
        transport=_StarletteTransport(),
    )
    created = client.upsert_identity(_upsert())
    assert created.external_id == "usr_abc"
    assert created.credential_present is True
    fetched = client.get_identity("usr_abc")
    assert fetched is not None
    assert fetched.email == "a@example.com"
    assert "hashed_password" not in fetched.model_dump()
    by_email = client.get_identity_by_email("A@example.com")
    assert by_email is not None
    assert by_email.external_id == "usr_abc"
    patched = client.patch_identity("usr_abc", IdentityPatch(admin=True))
    assert patched.admin is True
    assert patched.credential_present is True
    other_hash = "$2b$12$" + ("c" * 53)
    hashed = client.patch_identity(
        "usr_abc", IdentityPatch(hashed_password=other_hash)
    )
    assert hashed.credential_present is True
    with pytest.raises(IdentityClientError) as exc_info:
        client.create_identity(_upsert())
    assert exc_info.value.status_code == 409
    client.close()
    reset_stub()


def test_stub_retries_credential_store_then_succeeds() -> None:
    reset_stub()
    set_credential_store_failures(1)
    client = HttpIdentityClient(
        IdentityClientConfig(
            base_url="http://id.test",
            api_token=STUB_ACCESS_TOKEN,
        ),
        transport=_StarletteTransport(),
    )
    created = client.upsert_identity(_upsert())
    assert created.credential_present is True
    client.close()
    reset_stub()


def test_stub_rejects_bad_token() -> None:
    reset_stub()
    from starlette.testclient import TestClient

    with TestClient(app) as inner:
        response = inner.get(
            "/api/v1/identities/usr_x",
            headers={"Authorization": "Bearer wrong"},
        )
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"
    assert response.headers["www-authenticate"] == 'Bearer realm="idp"'
    reset_stub()


def test_stub_put_collection_and_get_by_email() -> None:
    reset_stub()
    from starlette.testclient import TestClient

    payload = _upsert().request_body()
    with TestClient(app) as inner:
        created = inner.put(
            "/api/v1/identities",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
            json=payload,
        )
        assert created.status_code == 201
        body = created.json()
        assert body["credential_present"] is True
        assert "hashed_password" not in body
        by_email = inner.get(
            "/api/v1/identities",
            params={"email": "A@Example.com"},
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
        )
        assert by_email.status_code == 200
        assert by_email.json()["external_id"] == "usr_abc"
        missing_email = inner.get(
            "/api/v1/identities",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
        )
        assert missing_email.status_code == 400
        posted = inner.post(
            "/api/v1/identities",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
            json={
                **payload,
                "external_id": "usr_def",
                "email": "b@example.com",
            },
        )
        assert posted.status_code == 201
        patched = inner.patch(
            "/api/v1/identities/usr_def",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
            json={"name": None},
        )
        assert patched.status_code == 200
        assert patched.json()["name"] is None
        assert patched.json()["credential_present"] is True
    reset_stub()


def test_stub_patch_without_hash_skips_credential_store() -> None:
    reset_stub()
    from starlette.testclient import TestClient

    with TestClient(app) as inner:
        created = inner.put(
            "/api/v1/identities/usr_abc",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
            json=_upsert().request_body(),
        )
        assert created.status_code == 201
        set_credential_store_failures(1)
        patched = inner.patch(
            "/api/v1/identities/usr_abc",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
            json={"admin": True},
        )
        assert patched.status_code == 200
        hashed = inner.patch(
            "/api/v1/identities/usr_abc",
            headers={"Authorization": f"Bearer {STUB_ACCESS_TOKEN}"},
            json={"hashed_password": HASH},
        )
        assert hashed.status_code == 502
        assert hashed.json()["error"] == "credential_store_unavailable"
    reset_stub()
