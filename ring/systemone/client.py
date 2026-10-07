"""Call the LLM service ``POST /systemone`` route.

Uses the existing generated ``ApiClient`` (host and ``X-API-Key``) so Ring
does not speak to TypeSafe directly. ``JEV_API_KEY`` stays on the LLM
service.
"""

from __future__ import annotations

from llm_service import ApiClient
from llm_service.exceptions import ApiException
from pydantic import ValidationError

from ring.fastapp.config import get_llm_config
from ring.systemone.schemas import SystemOneRequest, SystemOneResponse

# Jev is published at well under a second. The local wrapper is one chat
# completion, so allow longer than that without hanging a request worker.
_REQUEST_TIMEOUT_SECONDS = 30


class SystemOneClientError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def evaluate(request: SystemOneRequest) -> SystemOneResponse:
    """POST a System One request and parse the typed answers."""
    api_client = ApiClient(configuration=get_llm_config().config)
    serialized = api_client.param_serialize(
        method="POST",
        resource_path="/systemone",
        header_params={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body=request.model_dump(mode="json", exclude_none=True),
        auth_settings=["APIKeyHeader"],
    )
    try:
        response = api_client.call_api(
            *serialized,
            _request_timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except ApiException as exc:
        status_code = exc.status or 502
        raise SystemOneClientError(
            status_code, "System One request failed"
        ) from exc

    response.read()
    if response.status >= 400:
        raise SystemOneClientError(
            response.status, "System One request failed"
        )
    try:
        return SystemOneResponse.model_validate_json(response.data)
    except ValidationError as exc:
        raise SystemOneClientError(
            502, "System One returned an unexpected body"
        ) from exc
