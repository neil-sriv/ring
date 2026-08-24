"""Constants for the notifications domain."""

from __future__ import annotations

from enum import StrEnum


class NotificationType(StrEnum):
    """Type of an in-app notification.

    Each value corresponds to a product event that can notify users. Types
    mirror the transactional emails first (letter lifecycle, group
    membership) and expand to richer in-app events over time.
    """

    GENERIC = "generic"
    LETTER_SENT = "letter_sent"
    RESPONSES_OPEN = "responses_open"
    LETTER_REMINDER = "letter_reminder"
    AWAITING_RESPONSE = "awaiting_response"
    ADDED_TO_GROUP = "added_to_group"
    NEW_QUESTION = "new_question"
    NEW_RESPONSE = "new_response"
    MEMBER_JOINED = "member_joined"
