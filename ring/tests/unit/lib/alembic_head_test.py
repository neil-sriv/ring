"""Tests for the committed Alembic head pin."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from ring.lib.alembic_head import (
    HEAD_FILE,
    AlembicHeadError,
    check_committed_head,
    parse_revision_script,
    script_heads,
    write_committed_head,
    write_head_from_revision_script,
)


def _script(
    directory: Path,
    revision: str,
    down_revision: str | None,
    name: str | None = None,
) -> Path:
    down = "None" if down_revision is None else repr(down_revision)
    path = directory / f"{name or revision}.py"
    path.write_text(
        dedent(
            f"""\
            revision: str = {revision!r}
            down_revision: Union[str, None] = {down}
            """
        )
    )
    return path


class TestParseRevisionScript:
    def test_reads_string_down_revision(self, tmp_path: Path) -> None:
        path = _script(tmp_path, "bbb", "aaa")
        assert parse_revision_script(path) == ("bbb", ("aaa",))

    def test_reads_root_revision(self, tmp_path: Path) -> None:
        path = _script(tmp_path, "aaa", None)
        assert parse_revision_script(path) == ("aaa", ())

    def test_reads_merge_down_revision(self, tmp_path: Path) -> None:
        path = tmp_path / "merge.py"
        path.write_text(
            'revision: str = "ccc"\n'
            'down_revision: Union[str, None] = ("aaa", "bbb")\n'
        )
        assert parse_revision_script(path) == ("ccc", ("aaa", "bbb"))


class TestScriptHeads:
    def test_single_head(self, tmp_path: Path) -> None:
        _script(tmp_path, "aaa", None)
        _script(tmp_path, "bbb", "aaa")
        assert script_heads(tmp_path) == ["bbb"]

    def test_two_heads_from_same_parent(self, tmp_path: Path) -> None:
        _script(tmp_path, "aaa", None)
        _script(tmp_path, "bbb", "aaa")
        _script(tmp_path, "ccc", "aaa")
        assert script_heads(tmp_path) == ["bbb", "ccc"]


class TestCommittedHead:
    def test_write_from_new_script(self, tmp_path: Path) -> None:
        versions = tmp_path / "versions"
        versions.mkdir()
        head = tmp_path / "head"
        head.write_text("aaa\n")
        new = _script(versions, "bbb", "aaa")
        assert write_head_from_revision_script(new, head) == "bbb"
        assert head.read_text() == "bbb\n"

    def test_check_matches_single_head(self, tmp_path: Path) -> None:
        versions = tmp_path / "versions"
        versions.mkdir()
        _script(versions, "aaa", None)
        _script(versions, "bbb", "aaa")
        head = tmp_path / "head"
        head.write_text("bbb\n")
        assert check_committed_head(versions, head) == "bbb"

    def test_check_rejects_stale_pin(self, tmp_path: Path) -> None:
        versions = tmp_path / "versions"
        versions.mkdir()
        _script(versions, "aaa", None)
        _script(versions, "bbb", "aaa")
        head = tmp_path / "head"
        head.write_text("aaa\n")
        with pytest.raises(AlembicHeadError, match="alembic heads is 'bbb'"):
            check_committed_head(versions, head)

    def test_check_rejects_two_heads(self, tmp_path: Path) -> None:
        versions = tmp_path / "versions"
        versions.mkdir()
        _script(versions, "aaa", None)
        _script(versions, "bbb", "aaa")
        _script(versions, "ccc", "aaa")
        head = tmp_path / "head"
        head.write_text("bbb\n")
        with pytest.raises(AlembicHeadError, match="multiple heads"):
            check_committed_head(versions, head)

    def test_write_committed_head_requires_one_head(
        self, tmp_path: Path
    ) -> None:
        versions = tmp_path / "versions"
        versions.mkdir()
        _script(versions, "aaa", None)
        _script(versions, "bbb", "aaa")
        _script(versions, "ccc", "aaa")
        with pytest.raises(AlembicHeadError, match="exactly one head"):
            write_committed_head(versions, tmp_path / "head")


class TestRepoHeadFile:
    def test_committed_file_matches_script_heads(self) -> None:
        pinned = check_committed_head()
        assert HEAD_FILE.read_text() == f"{pinned}\n"
