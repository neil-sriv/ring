"""SPA paths for inbox targets.

Paths match the routes the frontend actually mounts. Group targets go to
``/groups/{id}/loops``; there is no ``/groups/{id}`` page.
"""

from __future__ import annotations

from ring.api_identifier.api_identified_model import APIPrefix


def inbox_href(target_api_id: str | None) -> str:
    """Return the in-app path for a notification target.

    Args:
        target_api_id: Weak reference such as ``lttr_…`` or ``grp_…``.

    Returns:
        A path beginning with ``/``. Unknown targets fall back to ``/``.
    """
    if not target_api_id or "_" not in target_api_id:
        return "/"
    prefix = target_api_id.split("_", 1)[0]
    if prefix == APIPrefix.LETTER.value:
        return f"/loops/{target_api_id}"
    if prefix == APIPrefix.GROUP.value:
        return f"/groups/{target_api_id}/loops"
    if prefix == APIPrefix.DOCUMENT.value:
        return f"/documents/{target_api_id}"
    return "/"
