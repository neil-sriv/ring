"""Collect Spotify track ids from letter and group content."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.parties.models.group_model import Group
from ring.spotify.tracks import extract_spotify_track_ids_from_parts


def letter_text_parts(letter: Letter) -> list[str | None]:
    """Title, then each question and its responses in display order."""
    parts: list[str | None] = [letter.title]
    questions = sorted(
        letter.questions, key=lambda question: question.position
    )
    for question in questions:
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
    """Load a group's letters in stable reading order.

    Numbered letters come first, lowest number first. Letters with no
    number (adhoc) follow, and equal keys break by primary key so a
    playlist sync does not reshuffle when the track set is unchanged.
    """
    return list(
        db.scalars(
            select(Letter)
            .where(Letter.group_id == group.id)
            .order_by(Letter.number.asc().nulls_last(), Letter.id.asc())
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
