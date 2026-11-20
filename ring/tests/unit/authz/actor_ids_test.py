"""Fail when a request field looks like a client-supplied actor id.

A body, query, or path field whose name matches ``author_*``, ``actor_*``,
``participant_*``, ``sender_*``, ``inviter_*``, ``admin_api_identifier``,
``user_api_id``, or ``user_api_identifier`` must be on the allowlist below
with a reason.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from ring.fastapp.fast import app

# method, path, location, name. location is "body", "query", or "path".
ActorFieldKey = tuple[str, str, str, str]

_ACTOR_FIELD = re.compile(
    r"^(?:author_|actor_|participant_|sender_|inviter_)"
    r"|(?:^admin_api_identifier$|^user_api_id$|^user_api_identifier$)"
)

# A1 and A2 stay until those fields are removed.
_DEPRECATED: dict[ActorFieldKey, str] = {
    (
        "post",
        "/letters/letter/{letter_api_id}:add_question",
        "body",
        "author_api_id",
    ): "A1. Author is the caller. Field removed in PR 5.",
    (
        "post",
        "/questions/question/{question_api_id}:upsert_response",
        "body",
        "participant_api_identifier",
    ): "A2. Participant is the caller. Field removed in PR 5.",
    (
        "post",
        "/parties/group",
        "body",
        "admin_api_identifier",
    ): "A3. Admin is the caller. Field removed in PR 5.",
    (
        "get",
        "/parties/groups/",
        "query",
        "user_api_id",
    ): "A4. Lists the caller. Field removed in PR 5.",
    (
        "post",
        "/notifications/subscription",
        "body",
        "user_api_identifier",
    ): "A5. Subscriber is the caller. Field removed in PR 5.",
}

# Target id on a role-gated route. Not the actor.
_TABLE_B: dict[ActorFieldKey, str] = {
    (
        "get",
        "/parties/user/{user_api_id}",
        "path",
        "user_api_id",
    ): "Table B. Admin reads another user.",
    (
        "patch",
        "/parties/user/{user_api_id}",
        "path",
        "user_api_id",
    ): "Table B. Admin renames another user.",
    (
        "patch",
        "/parties/{user_api_id}/admin",
        "path",
        "user_api_id",
    ): "Table B. Admin changes another user's admin flag.",
    (
        "post",
        "/impersonate-user-token",
        "query",
        "user_api_id",
    ): "Table B. Admin mints a token for another user.",
    (
        "post",
        "/parties/group/{group_api_id}:remove_member/{user_api_id}",
        "path",
        "user_api_id",
    ): "Table B. Group admin removes another member.",
}

# Pattern matches that are not the actor.
_NOT_THE_ACTOR: dict[ActorFieldKey, str] = {
    (
        "post",
        "/parties/group/{group_api_id}:add_member/{user_api_id}",
        "path",
        "user_api_id",
    ): "Target member in the path. Table C, not changed here.",
    (
        "get",
        "/search/raw-search",
        "query",
        "participant_api_id",
    ): "Search filter for whose responses to keep. Not the actor.",
    (
        "get",
        "/search/search",
        "query",
        "participant_api_id",
    ): "Search filter for whose responses to keep. Not the actor.",
}

ALLOWLIST: dict[ActorFieldKey, str] = {
    **_DEPRECATED,
    **_TABLE_B,
    **_NOT_THE_ACTOR,
}

# A1 and A3 to A5. A2 is left to the upsert change.
_OPTIONAL_DEPRECATED: frozenset[ActorFieldKey] = frozenset(
    key
    for key in _DEPRECATED
    if key[3]
    in {
        "author_api_id",
        "admin_api_identifier",
        "user_api_id",
        "user_api_identifier",
    }
)

_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _resolve(
    schema: dict[str, Any],
    components: dict[str, Any],
    seen: set[str],
) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema
    if ref in seen:
        return {}
    seen.add(ref)
    return components["schemas"][ref.rsplit("/", 1)[-1]]


def _collect(
    schema: dict[str, Any],
    components: dict[str, Any],
    seen: set[str],
) -> tuple[dict[str, Any], dict[str, Any], set[str]]:
    schema = _resolve(schema, components, seen)
    properties: dict[str, Any] = dict(schema.get("properties") or {})
    required = set(schema.get("required") or ())
    for combiner in ("allOf", "anyOf", "oneOf"):
        for sub in schema.get(combiner) or ():
            _, sub_properties, sub_required = _collect(sub, components, seen)
            properties.update(sub_properties)
            required.update(sub_required)
    return schema, properties, required


def _walk_body(
    schema: dict[str, Any],
    components: dict[str, Any],
    seen: set[str],
) -> Iterator[tuple[str, bool, bool]]:
    schema, properties, required = _collect(schema, components, seen)
    for name, prop in properties.items():
        yield name, name in required, bool(prop.get("deprecated"))
        yield from _walk_body(prop, components, seen)
    items = schema.get("items")
    if isinstance(items, dict):
        yield from _walk_body(items, components, seen)


def iter_actor_fields(
    spec: dict[str, Any],
) -> Iterator[tuple[ActorFieldKey, bool, bool]]:
    components = spec.get("components") or {}
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method not in _HTTP_METHODS:
                continue
            for param in operation.get("parameters") or []:
                name = param.get("name")
                location = param.get("in")
                if (
                    not isinstance(name, str)
                    or location not in {"path", "query"}
                    or _ACTOR_FIELD.search(name) is None
                ):
                    continue
                yield (
                    (method, path, location, name),
                    bool(param.get("required")),
                    bool(param.get("deprecated")),
                )
            body = (operation.get("requestBody") or {}).get("content") or {}
            for media in body.values():
                seen: set[str] = set()
                for name, required, deprecated in _walk_body(
                    media.get("schema") or {},
                    components,
                    seen,
                ):
                    if _ACTOR_FIELD.search(name) is None:
                        continue
                    yield (
                        (method, path, "body", name),
                        required,
                        deprecated,
                    )


def test_actor_id_fields_match_allowlist() -> None:
    """Every actor-shaped request field is allowlisted, and vice versa."""
    assert len(ALLOWLIST) == (
        len(_DEPRECATED) + len(_TABLE_B) + len(_NOT_THE_ACTOR)
    )
    found = {
        key: (required, deprecated)
        for key, required, deprecated in iter_actor_fields(app.openapi())
    }
    missing = sorted(set(found) - set(ALLOWLIST))
    stale = sorted(set(ALLOWLIST) - set(found))
    assert missing == [], f"actor id fields not on the allowlist: {missing}"
    assert stale == [], f"allowlist entries no longer in the schema: {stale}"
    for key in _OPTIONAL_DEPRECATED:
        required, deprecated = found[key]
        assert required is False, key
        assert deprecated is True, key
