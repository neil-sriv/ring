from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

_IDENTITY_PATH = "/api/v1/identities/{external_id}"
_RETRYABLE_ERROR = "credential_store_unavailable"


def format_created_at(value: datetime | None) -> str:
    instant = _as_utc(value if value is not None else datetime.now(UTC))
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


def created_at_equal(
    left: datetime | str | None,
    right: datetime | str | None,
) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return _as_utc(left) == _as_utc(right)


def _as_utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    else:
        parsed = value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0)


def _identity_path(external_id: str) -> str:
    return _IDENTITY_PATH.format(
        external_id=urllib.parse.quote(external_id, safe="")
    )


@dataclass(frozen=True)
class IdentityClientConfig:
    base_url: str
    api_token: str
    timeout_seconds: float = 2.0
    write_retries: int = 3

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_token)


@dataclass(frozen=True)
class Identity:
    id: str
    external_id: str
    email: str
    name: str | None
    admin: bool
    credential_present: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class IdentityUpsert:
    external_id: str
    email: str
    name: str | None
    hashed_password: str
    admin: bool
    created_at: str

    def __post_init__(self) -> None:
        password = self.hashed_password
        if (
            not isinstance(password, str)
            or not 20 <= len(password) <= 512
            or not password.startswith("$")
        ):
            raise ValueError("hashed_password must start with $")

    def request_body(self) -> dict[str, object]:
        return {
            "external_id": self.external_id,
            "email": self.email,
            "name": self.name,
            "hashed_password": self.hashed_password,
            "admin": self.admin,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return (
            "IdentityUpsert("
            f"external_id={self.external_id!r}, email={self.email!r}, "
            f"name={self.name!r}, admin={self.admin!r}, "
            f"created_at={self.created_at!r})"
        )


class IdentityClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        path: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.path = path
        self.error = error
        self.error_description = error_description


class IdentityClient(Protocol):
    def upsert_identity(self, payload: IdentityUpsert) -> Identity: ...

    def get_identity(self, external_id: str) -> Identity | None: ...


class HttpIdentityClient:
    def __init__(self, config: IdentityClientConfig) -> None:
        self._config = config

    def close(self) -> None:
        return None

    def upsert_identity(self, payload: IdentityUpsert) -> Identity:
        path = _identity_path(payload.external_id)
        raw = self._request(
            "PUT", path, payload.request_body(), retry=True
        )
        return _parse_identity(raw, path)

    def get_identity(self, external_id: str) -> Identity | None:
        path = _identity_path(external_id)
        raw = self._request("GET", path, None, retry=False, allow_404=True)
        if raw is None:
            return None
        return _parse_identity(raw, path)

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None,
        *,
        retry: bool,
        allow_404: bool = False,
    ) -> bytes | None:
        attempts = self._config.write_retries if retry else 1
        last_error: IdentityClientError | None = None
        for attempt in range(attempts):
            try:
                return self._send(
                    method, path, body, allow_404=allow_404
                )
            except IdentityClientError as exc:
                last_error = exc
                retryable = (
                    retry
                    and exc.status_code == 502
                    and exc.error == _RETRYABLE_ERROR
                    and attempt + 1 < attempts
                )
                if not retryable:
                    raise
        if last_error is not None:
            raise last_error
        raise IdentityClientError(
            f"no attempt calling {method} {path}", path=path
        )

    def _send(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None,
        *,
        allow_404: bool,
    ) -> bytes | None:
        url = f"{self._config.base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {self._config.api_token}"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self._config.timeout_seconds
            ) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            if allow_404 and exc.code == 404:
                return None
            error, description = _error_fields(raw)
            detail = f" error={error}" if error else ""
            raise IdentityClientError(
                f"http {exc.code} calling {method} {path}{detail}",
                status_code=exc.code,
                path=path,
                error=error,
                error_description=description,
            ) from exc
        except TimeoutError as exc:
            raise IdentityClientError(
                f"timeout calling {method} {path}", path=path
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise IdentityClientError(
                    f"timeout calling {method} {path}", path=path
                ) from exc
            raise IdentityClientError(
                f"transport error calling {method} {path}", path=path
            ) from exc


def _parse_identity(raw: bytes, path: str) -> Identity:
    try:
        body = json.loads(raw)
    except ValueError as exc:
        raise IdentityClientError(
            f"invalid JSON from {path}", path=path
        ) from exc
    if not isinstance(body, dict):
        raise IdentityClientError(
            f"invalid identity response from {path}", path=path
        )
    if "hashed_password" in body:
        raise IdentityClientError(
            f"identity response from {path} included hashed_password",
            path=path,
        )
    try:
        name = body["name"]
        if name is not None and not isinstance(name, str):
            raise TypeError("name")
        admin = body["admin"]
        present = body["credential_present"]
        if type(admin) is not bool or type(present) is not bool:
            raise TypeError("bool")
        return Identity(
            id=_text(body, "id"),
            external_id=_text(body, "external_id"),
            email=_text(body, "email"),
            name=name,
            admin=admin,
            credential_present=present,
            created_at=_text(body, "created_at"),
            updated_at=_text(body, "updated_at"),
        )
    except (KeyError, TypeError) as exc:
        raise IdentityClientError(
            f"invalid identity response from {path}", path=path
        ) from exc


def _text(body: dict[str, object], key: str) -> str:
    value = body[key]
    if not isinstance(value, str):
        raise TypeError(key)
    return value


def _error_fields(raw: bytes) -> tuple[str | None, str | None]:
    try:
        body = json.loads(raw)
    except ValueError:
        return None, None
    if not isinstance(body, dict):
        return None, None
    error = body.get("error")
    description = body.get("error_description")
    return (
        error if isinstance(error, str) else None,
        description if isinstance(description, str) else None,
    )
