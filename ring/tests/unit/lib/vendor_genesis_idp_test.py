"""Offline checksum check for vendored genesis-idp."""

from __future__ import annotations

from pathlib import Path

from ring.lib.vendor_genesis_idp import (
    check_vendored_tree,
    parse_manifest,
    render_manifest,
    write_manifest,
)


def test_committed_manifest_matches_tree() -> None:
    assert check_vendored_tree() == ""


def test_hand_edit_is_detected(tmp_path: Path) -> None:
    package = tmp_path / "genesis_idp"
    package.mkdir()
    (package / "hello.py").write_text("x = 1\n")
    manifest = tmp_path / "genesis_idp.sha256"
    write_manifest(package, manifest)
    assert check_vendored_tree(package, manifest) == ""
    (package / "hello.py").write_text("x = 2\n")
    assert "modified hello.py" in check_vendored_tree(package, manifest)
    (package / "extra.py").write_text("y = 1\n")
    diff = check_vendored_tree(package, manifest)
    assert "untracked extra.py" in diff
    (package / "hello.py").unlink()
    diff = check_vendored_tree(package, manifest)
    assert "missing hello.py" in diff


def test_manifest_round_trip() -> None:
    rendered = render_manifest()
    entries = parse_manifest(rendered)
    assert "VENDORED_FROM" in entries
    assert "__init__.py" in entries
    assert "stub.py" in entries
    assert "aio.py" not in entries
