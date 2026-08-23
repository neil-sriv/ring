from __future__ import annotations

import re
from dataclasses import dataclass

from ring.letters.constants import LetterStatus

QUALIFIER_RE = re.compile(
    r"""
    (?P<qualifier>
        (?P<key>author|status|is)
        :
        (?:
            "(?P<quoted>[^"]*)"
            |
            (?P<bare>\S+)
        )
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

AUTHOR_ME_RE = re.compile(
    r'(?i)(?<!\S)author:(?:"@me"|@me)(?!\S)',
)

STATUS_ALIASES: dict[str, LetterStatus] = {
    "open": LetterStatus.IN_PROGRESS,
    "in_progress": LetterStatus.IN_PROGRESS,
    "in-progress": LetterStatus.IN_PROGRESS,
    "current": LetterStatus.IN_PROGRESS,
    "active": LetterStatus.IN_PROGRESS,
    "published": LetterStatus.SENT,
    "sent": LetterStatus.SENT,
    "closed": LetterStatus.SENT,
    "upcoming": LetterStatus.UPCOMING,
    "scheduled": LetterStatus.UPCOMING,
}


@dataclass(frozen=True)
class ParsedSearchQuery:
    text: str
    authors: tuple[str, ...]
    statuses: tuple[LetterStatus, ...]
    match_nothing: bool = False


def expand_author_me(query: str, author_value: str) -> str:
    """Replace GitHub-style author:@me with a concrete author value."""
    replacement = f'author:"{author_value}"'
    return AUTHOR_ME_RE.sub(replacement, query)


def parse_search_query(query: str) -> ParsedSearchQuery:
    """Parse GitHub-style search qualifiers from a free-text query.

    Supported qualifiers:
    - author:name / author:"Full Name" — match question authors or response
      participants (substring, case-insensitive on name or email)
    - status:open|published|upcoming — match letters and their questions/responses
    - is:open|published|upcoming — alias of status:
    """
    authors: list[str] = []
    statuses: list[LetterStatus] = []
    saw_status_qualifier = False
    saw_invalid_status = False

    def _replace(match: re.Match[str]) -> str:
        nonlocal saw_status_qualifier, saw_invalid_status
        key = match.group("key").lower()
        raw_value = match.group("quoted")
        if raw_value is None:
            raw_value = match.group("bare") or ""
        value = raw_value.strip()
        if key == "author":
            if value:
                authors.append(value)
            return " "
        saw_status_qualifier = True
        status = _parse_status_value(value)
        if status is None:
            saw_invalid_status = True
        else:
            statuses.append(status)
        return " "

    remainder = QUALIFIER_RE.sub(_replace, query)
    text = " ".join(remainder.split())
    unique_authors = tuple(dict.fromkeys(authors))
    unique_statuses = tuple(dict.fromkeys(statuses))
    match_nothing = saw_status_qualifier and not unique_statuses
    if saw_invalid_status and not unique_statuses:
        match_nothing = True
    return ParsedSearchQuery(
        text=text,
        authors=unique_authors,
        statuses=unique_statuses,
        match_nothing=match_nothing,
    )


def _parse_status_value(value: str) -> LetterStatus | None:
    normalized = value.strip().lower().replace(" ", "_")
    if normalized in STATUS_ALIASES:
        return STATUS_ALIASES[normalized]
    for status in LetterStatus:
        if status.value.lower() == normalized:
            return status
    return None
