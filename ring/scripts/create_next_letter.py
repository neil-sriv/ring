"""Create the next upcoming cyclic letter for a group.

Invoked by ``ring letters create-next GROUP_API_ID``.
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from ring.api_identifier.util import IDNotFoundException
from ring.letters.crud.create_next import (
    CreateNextLetterError,
    create_next_cyclic_letter,
)
from ring.scripts.dependencies import get_script_dependencies


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create the next upcoming cyclic letter for a group, with "
            "defaults + 3 bank questions. No-ops if one already exists."
        )
    )
    parser.add_argument(
        "group_api_id",
        help="Group API identifier (grp_...)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create in the current transaction and roll it back",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    deps = get_script_dependencies()
    db = deps.db
    try:
        letter = create_next_cyclic_letter(db, args.group_api_id)
        db.flush()
        message = "upcoming letter {} #{} for group {} ({} questions)".format(
            letter.api_identifier,
            letter.number,
            args.group_api_id,
            len(letter.questions),
        )
        if args.dry_run:
            db.rollback()
            logger.info("dry-run: would ensure {}", message)
        else:
            db.commit()
            logger.info("ensured {}", message)
        return 0
    except IDNotFoundException as exc:
        db.rollback()
        logger.error(exc.detail or str(exc))
        return 1
    except CreateNextLetterError as exc:
        db.rollback()
        logger.error(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(run())
