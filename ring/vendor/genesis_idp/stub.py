"""Local IdP HTTP stub matching identity API v2.

Used by tests and for flag-on verification without genesis:

    uvicorn ring.vendor.genesis_idp.stub:app --port 4465
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .paths import DEFAULT_COLLECTION_PATH
from .times import format_created_at

STUB_ACCESS_TOKEN = "ring-idp-directory-token-32chars"
_STORE: dict[str, dict[str, Any]] = {}
_HASHES: dict[str, str] = {}
_CREDENTIAL_FAILS_REMAINING = 0
_ALLOWED_WRITE_FIELDS = {
    "external_id",
    "email",
    "name",
    "hashed_password",
    "admin",
    "created_at",
    "id",
    "updated_at",
    "credential_present",
}


def reset_stub() -> None:
    """Clear in-memory identities (tests)."""
    global _CREDENTIAL_FAILS_REMAINING
    _STORE.clear()
    _HASHES.clear()
    _CREDENTIAL_FAILS_REMAINING = 0


def set_credential_store_failures(count: int) -> None:
    """Next ``count`` writes return 502 credential_store_unavailable."""
    global _CREDENTIAL_FAILS_REMAINING
    _CREDENTIAL_FAILS_REMAINING = count


def _error(status: int, error: str, description: str) -> JSONResponse:
    headers = {"Cache-Control": "no-store"}
    if status == 401:
        headers["WWW-Authenticate"] = 'Bearer realm="idp"'
    return JSONResponse(
        {"error": error, "error_description": description},
        status_code=status,
        headers=headers,
    )


def _require_bearer(request: Request) -> JSONResponse | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or token != STUB_ACCESS_TOKEN:
        return _error(
            401,
            "unauthorized",
            "bearer token is missing or invalid",
        )
    return None


def _identity_json(record: dict[str, Any]) -> dict[str, Any]:
    external_id = record["external_id"]
    return {
        "id": record["id"],
        "external_id": external_id,
        "email": record["email"],
        "name": record.get("name"),
        "admin": bool(record["admin"]),
        "credential_present": external_id in _HASHES,
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
    }


def _maybe_credential_fail() -> JSONResponse | None:
    global _CREDENTIAL_FAILS_REMAINING
    if _CREDENTIAL_FAILS_REMAINING <= 0:
        return None
    _CREDENTIAL_FAILS_REMAINING -= 1
    return _error(
        502,
        "credential_store_unavailable",
        "credential store unavailable",
    )


async def _read_json_object(request: Request) -> dict[str, Any] | JSONResponse:
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        return _error(400, "invalid_request", "expected application/json")
    try:
        body = await request.json()
    except Exception:
        return _error(400, "invalid_request", "malformed JSON")
    if not isinstance(body, dict):
        return _error(400, "invalid_request", "malformed JSON")
    extra = set(body) - _ALLOWED_WRITE_FIELDS
    if extra:
        return _error(400, "invalid_request", "unknown field")
    return body


def _normalize_name(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if isinstance(value, str):
        return value
    return None


def _upsert_from_body(
    external_id: str, body: dict[str, Any], *, create_only: bool
) -> Response:
    body_external_id = body.get("external_id")
    if body_external_id is not None and body_external_id != external_id:
        return _error(400, "invalid_request", "path/body id mismatch")
    email = body.get("email")
    hashed_password = body.get("hashed_password")
    if not isinstance(email, str) or not email:
        return _error(400, "invalid_request", "email is invalid")
    if "admin" not in body or not isinstance(body.get("admin"), bool):
        return _error(400, "invalid_request", "admin is required")
    if (
        not isinstance(hashed_password, str)
        or not hashed_password.startswith("$")
        or not 20 <= len(hashed_password) <= 512
    ):
        return _error(400, "invalid_request", "plaintext password")
    created_at = body.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        return _error(400, "invalid_request", "created_at is required")
    existing = _STORE.get(external_id)
    if create_only and existing is not None:
        return _error(409, "conflict", "external_id already exists")
    email_norm = email.lower().strip()
    for other_id, record in _STORE.items():
        if other_id == external_id:
            continue
        if str(record["email"]).lower() == email_norm:
            return _error(409, "conflict", "email already exists")
    failed = _maybe_credential_fail()
    if failed is not None:
        return failed
    name = _normalize_name(body.get("name"))
    now = format_created_at(datetime.now(UTC))
    if existing is None:
        record = {
            "id": f"usr_stub_{external_id[4:12]}",
            "external_id": external_id,
            "email": email.lower().strip(),
            "name": name,
            "admin": body["admin"],
            "created_at": created_at,
            "updated_at": now,
        }
        _STORE[external_id] = record
        _HASHES[external_id] = hashed_password
        return JSONResponse(
            _identity_json(record),
            status_code=201,
            headers={
                "Location": f"/api/v1/identities/{external_id}",
                "Cache-Control": "no-store",
            },
        )
    existing.update(
        {
            "email": email.lower().strip(),
            "name": name,
            "admin": body["admin"],
            "updated_at": now,
        }
    )
    _HASHES[external_id] = hashed_password
    return JSONResponse(
        _identity_json(existing),
        headers={"Cache-Control": "no-store"},
    )


async def put_identity(request: Request) -> Response:
    denied = _require_bearer(request)
    if denied is not None:
        return denied
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return _upsert_from_body(
        request.path_params["external_id"],
        body,
        create_only=False,
    )


async def put_identity_collection(request: Request) -> Response:
    denied = _require_bearer(request)
    if denied is not None:
        return denied
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    external_id = body.get("external_id")
    if not isinstance(external_id, str) or not external_id:
        return _error(400, "invalid_request", "external_id is required")
    return _upsert_from_body(external_id, body, create_only=False)


async def post_identity(request: Request) -> Response:
    denied = _require_bearer(request)
    if denied is not None:
        return denied
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    external_id = body.get("external_id")
    if not isinstance(external_id, str) or not external_id:
        return _error(400, "invalid_request", "external_id is required")
    return _upsert_from_body(external_id, body, create_only=True)


async def patch_identity(request: Request) -> Response:
    denied = _require_bearer(request)
    if denied is not None:
        return denied
    body = await _read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    external_id = request.path_params["external_id"]
    existing = _STORE.get(external_id)
    if existing is None:
        return _error(404, "not_found", "identity not found")
    hashed_password = body.get("hashed_password")
    if "hashed_password" in body:
        if (
            not isinstance(hashed_password, str)
            or not hashed_password.startswith("$")
            or not 20 <= len(hashed_password) <= 512
        ):
            return _error(400, "invalid_request", "plaintext password")
        failed = _maybe_credential_fail()
        if failed is not None:
            return failed
        _HASHES[external_id] = hashed_password
    if "email" in body and isinstance(body["email"], str):
        existing["email"] = body["email"].lower().strip()
    if "name" in body:
        existing["name"] = _normalize_name(body["name"])
    if "admin" in body and isinstance(body["admin"], bool):
        existing["admin"] = body["admin"]
    existing["updated_at"] = format_created_at(datetime.now(UTC))
    return JSONResponse(
        _identity_json(existing),
        headers={"Cache-Control": "no-store"},
    )


async def get_identity(request: Request) -> Response:
    denied = _require_bearer(request)
    if denied is not None:
        return denied
    external_id = request.path_params["external_id"]
    record = _STORE.get(external_id)
    if record is None:
        return _error(404, "not_found", "identity not found")
    return JSONResponse(
        _identity_json(record),
        headers={"Cache-Control": "no-store"},
    )


async def list_identities(request: Request) -> Response:
    denied = _require_bearer(request)
    if denied is not None:
        return denied
    email = request.query_params.get("email")
    if not email:
        return _error(400, "invalid_request", "email is required")
    needle = email.lower()
    for record in _STORE.values():
        if str(record["email"]).lower() == needle:
            return JSONResponse(
                _identity_json(record),
                headers={"Cache-Control": "no-store"},
            )
    return _error(404, "not_found", "identity not found")


app = Starlette(
    routes=[
        Route(
            "/api/v1/identities/{external_id}",
            put_identity,
            methods=["PUT"],
        ),
        Route(
            "/api/v1/identities/{external_id}",
            patch_identity,
            methods=["PATCH"],
        ),
        Route(
            "/api/v1/identities/{external_id}",
            get_identity,
            methods=["GET"],
        ),
        Route(
            DEFAULT_COLLECTION_PATH,
            put_identity_collection,
            methods=["PUT"],
        ),
        Route(
            DEFAULT_COLLECTION_PATH,
            post_identity,
            methods=["POST"],
        ),
        Route(
            DEFAULT_COLLECTION_PATH,
            list_identities,
            methods=["GET"],
        ),
    ]
)
