"""HTTP IdentityClient for the locked IdP identity API (v2).

Auth is ``Authorization: Bearer $IDP_DIRECTORY_API_TOKEN``. Ring never calls
AuthN. Write calls retry ``502 credential_store_unavailable``.
"""

from __future__ import annotations

from typing import Any

import httpx

from ring.auth.idp_client.config import IdentityClientConfig
from ring.auth.idp_client.errors import IdentityClientError
from ring.auth.idp_client.models import Identity, IdentityPatch, IdentityUpsert

_RETRYABLE_ERROR = "credential_store_unavailable"


def _join(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


class HttpIdentityClient:
    """Sync httpx client for IdP identity upsert, GET, POST, and PATCH."""

    def __init__(
        self,
        config: IdentityClientConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        http: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._owns_http = http is None
        timeout = httpx.Timeout(config.timeout_seconds)
        self._http = http or httpx.Client(
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def upsert_identity(self, payload: IdentityUpsert) -> Identity:
        path = self._config.identity_path.format(
            external_id=payload.external_id
        )
        response = self._request(
            "PUT",
            path,
            json_body=payload.request_body(),
            retry_writes=True,
        )
        return self._parse_identity(response, path)

    def create_identity(self, payload: IdentityUpsert) -> Identity:
        path = self._config.collection_path
        response = self._request(
            "POST",
            path,
            json_body=payload.request_body(),
            retry_writes=True,
        )
        return self._parse_identity(response, path)

    def patch_identity(
        self, external_id: str, payload: IdentityPatch
    ) -> Identity:
        path = self._config.identity_path.format(external_id=external_id)
        response = self._request(
            "PATCH",
            path,
            json_body=payload.request_body(),
            retry_writes=True,
        )
        return self._parse_identity(response, path)

    def get_identity(self, external_id: str) -> Identity | None:
        path = self._config.identity_path.format(external_id=external_id)
        response = self._request("GET", path, allow_404=True)
        if response.status_code == 404:
            return None
        return self._parse_identity(response, path)

    def get_identity_by_email(self, email: str) -> Identity | None:
        response = self._request(
            "GET",
            self._config.collection_path,
            params={"email": email},
            allow_404=True,
        )
        if response.status_code == 404:
            return None
        return self._parse_identity(response, self._config.collection_path)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
        allow_404: bool = False,
        retry_writes: bool = False,
    ) -> httpx.Response:
        attempts = self._config.write_retries if retry_writes else 1
        last_error: IdentityClientError | None = None
        for attempt in range(attempts):
            try:
                return self._send(
                    method,
                    path,
                    json_body=json_body,
                    params=params,
                    allow_404=allow_404,
                )
            except IdentityClientError as exc:
                last_error = exc
                retryable = (
                    retry_writes
                    and exc.status_code == 502
                    and exc.error == _RETRYABLE_ERROR
                    and attempt + 1 < attempts
                )
                if not retryable:
                    raise
        assert last_error is not None
        raise last_error

    def _send(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, object] | None,
        params: dict[str, str] | None,
        allow_404: bool,
    ) -> httpx.Response:
        url = _join(self._config.base_url, path)
        headers = {
            "Authorization": f"Bearer {self._config.api_token}",
        }
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        try:
            response = self._http.request(
                method,
                url,
                headers=headers,
                json=json_body,
                params=params,
            )
        except httpx.TimeoutException as exc:
            raise IdentityClientError(
                f"timeout calling {method} {path}",
                path=path,
            ) from exc
        except httpx.HTTPError as exc:
            raise IdentityClientError(
                f"transport error calling {method} {path}",
                path=path,
            ) from exc
        if allow_404 and response.status_code == 404:
            return response
        if response.status_code >= 400:
            error, description = _error_fields(response)
            raise IdentityClientError(
                f"http {response.status_code} calling {method} {path}"
                + (f" error={error}" if error else ""),
                status_code=response.status_code,
                path=path,
                error=error,
                error_description=description,
            )
        return response

    def _parse_identity(self, response: httpx.Response, path: str) -> Identity:
        try:
            body: Any = response.json()
        except ValueError as exc:
            raise IdentityClientError(
                f"invalid JSON from {path}",
                path=path,
            ) from exc
        if isinstance(body, dict) and "hashed_password" in body:
            raise IdentityClientError(
                f"identity response from {path} included hashed_password",
                path=path,
            )
        try:
            return Identity.model_validate(body)
        except Exception as exc:
            raise IdentityClientError(
                f"invalid identity response from {path}",
                path=path,
            ) from exc


def _error_fields(response: httpx.Response) -> tuple[str | None, str | None]:
    try:
        body: Any = response.json()
    except ValueError:
        return None, None
    if not isinstance(body, dict):
        return None, None
    error = body.get("error")
    description = body.get("error_description")
    error_text = error if isinstance(error, str) else None
    description_text = description if isinstance(description, str) else None
    return error_text, description_text
