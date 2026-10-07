"""Committed Alembic head pin so concurrent migration PRs git-conflict.

``ring/alembic/head`` holds the current head revision id. Every new
revision must replace that line. Two PRs that fork the same parent both
rewrite the same one-line file, so GitHub reports ``CONFLICTING`` instead
of remaining MERGEABLE with two Alembic heads.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

HEAD_FILE = Path(__file__).resolve().parents[1] / "alembic" / "head"
VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"

_ASSIGNMENT_RE = re.compile(r"^([A-Za-z_]+):\s*[^\n=]*=\s*(.+)$", re.M)


class AlembicHeadError(ValueError):
    """The committed head file does not match the script directory."""


def _assignment(source: str, name: str, path: Path) -> object:
    for match in _ASSIGNMENT_RE.finditer(source):
        if match.group(1) == name:
            return ast.literal_eval(match.group(2).strip())
    raise AlembicHeadError(f"{path} has no {name} assignment")


def parse_revision_script(path: Path) -> tuple[str, tuple[str, ...]]:
    """Return ``(revision, down_revisions)`` from an Alembic script."""
    source = path.read_text()
    revision = _assignment(source, "revision", path)
    if not isinstance(revision, str) or not revision:
        raise AlembicHeadError(f"{path} revision must be a non-empty string")
    down = _assignment(source, "down_revision", path)
    if down is None:
        return revision, ()
    if isinstance(down, str):
        return revision, (down,)
    if isinstance(down, tuple) and all(isinstance(item, str) for item in down):
        return revision, down
    raise AlembicHeadError(f"{path} has an unsupported down_revision")


def script_revisions(
    versions_dir: Path = VERSIONS_DIR,
) -> dict[str, tuple[str, ...]]:
    """Map each revision id in ``versions_dir`` to its parents."""
    revisions: dict[str, tuple[str, ...]] = {}
    for path in sorted(versions_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        revision, downs = parse_revision_script(path)
        if revision in revisions:
            raise AlembicHeadError(f"duplicate revision id {revision}")
        revisions[revision] = downs
    return revisions


def script_heads(versions_dir: Path = VERSIONS_DIR) -> list[str]:
    """Revision ids that are not anyone else's ``down_revision``."""
    revisions = script_revisions(versions_dir)
    parents = {parent for downs in revisions.values() for parent in downs}
    return sorted(
        revision for revision in revisions if revision not in parents
    )


def read_head_file(path: Path = HEAD_FILE) -> str:
    """Return the pinned revision id from the committed head file."""
    if not path.is_file():
        raise AlembicHeadError(f"{path} is missing")
    revision = path.read_text().strip()
    if not revision or any(ch.isspace() for ch in revision):
        raise AlembicHeadError(f"{path} must contain a single revision id")
    return revision


def write_head_file(revision: str, path: Path = HEAD_FILE) -> None:
    """Pin ``path`` to ``revision`` (single line, trailing newline)."""
    if not revision or any(ch.isspace() for ch in revision):
        raise AlembicHeadError("revision must be a single token")
    path.write_text(f"{revision}\n")


def write_head_from_revision_script(
    revision_path: Path, path: Path = HEAD_FILE
) -> str:
    """Pin the head file to the revision in a newly generated script."""
    revision, _downs = parse_revision_script(revision_path)
    write_head_file(revision, path)
    return revision


def write_committed_head(
    versions_dir: Path = VERSIONS_DIR, path: Path = HEAD_FILE
) -> str:
    """Pin the head file to the sole script-directory head."""
    heads = script_heads(versions_dir)
    if len(heads) != 1:
        raise AlembicHeadError(
            "Alembic must have exactly one head to pin "
            f"{path.name}; found {heads or 'none'}"
        )
    write_head_file(heads[0], path)
    return heads[0]


def check_committed_head(
    versions_dir: Path = VERSIONS_DIR, path: Path = HEAD_FILE
) -> str:
    """Require the committed file to match ``alembic heads``.

    Raises:
        AlembicHeadError: multiple heads, a missing file, or a mismatch.
    """
    heads = script_heads(versions_dir)
    if len(heads) != 1:
        raise AlembicHeadError(
            "Alembic has multiple heads: "
            f"{', '.join(heads) or 'none'}. Rebase one revision's "
            "down_revision onto the other and pin ring/alembic/head "
            "to the remaining head."
        )
    pinned = read_head_file(path)
    if pinned != heads[0]:
        raise AlembicHeadError(
            f"ring/alembic/head is {pinned!r} but alembic heads is "
            f"{heads[0]!r}. After adding a revision, pin the file to "
            "the new id (`ring db generate` does this)."
        )
    return pinned


def main(argv: list[str] | None = None) -> None:
    """Alembic ``post_write_hooks`` entry: ``python -m ring.lib.alembic_head``."""
    args = sys.argv[1:] if argv is None else argv
    if args:
        write_head_from_revision_script(Path(args[0]))
        return
    write_committed_head()


if __name__ == "__main__":
    main()
