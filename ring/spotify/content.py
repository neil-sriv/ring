"""Collect Spotify track ids from letter and group content."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.parties.models.group_model import Group
from ring.spotify.tracks import extract_spotify_track_ids_from_parts


def letter_text_parts(letter: Letter) -> list[str | None]:
    """Title, question text, and response text for one letter."""
    parts: list[str | None] = [letter.title]
    for question in letter.questions:
        parts.append(question.question_text)
        for response in question.responses:
            parts.append(response.response_text)
    return parts


def letter_track_ids(letter: Letter) -> list[str]:
    """Unique Spotify track ids that appear in a letter."""
    return extract_spotify_track_ids_from_parts(letter_text_parts(letter))


def load_letter_with_content(db: Session, letter: Letter) -> Letter:
    """Reload a letter with questions and responses."""
    return db.scalars(
        select(Letter)
        .where(Letter.id == letter.id)
        .options(
            selectinload(Letter.questions).selectinload(Question.responses)
        )
    ).one()


def load_group_letters(db: Session, group: Group) -> list[Letter]:
    """Load every letter in a group with questions and responses."""
    return list(
        db.scalars(
            select(Letter)
            .where(Letter.group_id == group.id)
            .options(
                selectinload(Letter.questions).selectinload(Question.responses)
            )
        ).all()
    )


def group_track_ids(letters: list[Letter]) -> list[str]:
    """Unique track ids across letters, in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for letter in letters:
        for track_id in letter_track_ids(letter):
            if track_id not in seen:
                seen.add(track_id)
                ordered.append(track_id)
    return ordered
