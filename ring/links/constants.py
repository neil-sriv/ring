"""Constants and helpers for short links.

Defines which resources may be shared behind a short link and how an
``api_identifier`` maps to a coarse target type used by clients to route the
redirect.
"""

from __future__ import annotations

from enum import StrEnum

from ring.api_identifier.api_identified_model import APIPrefix


class ShortLinkTargetType(StrEnum):
    """Coarse category of a short link's target resource."""

    LETTER = "letter"


# API prefixes that are allowed to be shared behind a short link, mapped to the
# coarse target type clients use to route the redirect. Extend this mapping to
# support sharing additional resource types.
SHAREABLE_PREFIX_TO_TARGET_TYPE: dict[APIPrefix, ShortLinkTargetType] = {
    APIPrefix.LETTER: ShortLinkTargetType.LETTER,
}


def target_type_for_api_id(api_id: str) -> ShortLinkTargetType | None:
    """Return the short link target type for an api identifier, if shareable.

    Args:
        api_id (str): The resource api identifier (e.g. ``lttr_<uuid>``).

    Returns:
        ShortLinkTargetType | None: The mapped target type, or ``None`` when the
            resource type cannot be shared behind a short link.
    """
    prefix_str = api_id.split("_", 1)[0]
    try:
        prefix = APIPrefix(prefix_str)
    except ValueError:
        return None
    return SHAREABLE_PREFIX_TO_TARGET_TYPE.get(prefix)
