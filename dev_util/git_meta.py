"""Host-side git metadata for Docker build args and compose interpolation."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from dev_util.dev import ROOT_DIR


def _sanitize(value: str) -> str:
    return " ".join(value.split())[:500]


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def collect_host_git_build_args(
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Return RING_GIT_* values from the host checkout."""
    root = repo_root or ROOT_DIR
    sha = _git(root, "rev-parse", "HEAD")
    dirty = _git(root, "status", "--porcelain")
    return {
        "RING_GIT_SHA": sha,
        "RING_GIT_SHORT_SHA": _git(root, "rev-parse", "--short", "HEAD"),
        "RING_GIT_BRANCH": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "RING_GIT_SUBJECT": _sanitize(
            _git(root, "log", "-1", "--pretty=format:%s")
        ),
        "RING_GIT_AUTHOR_NAME": _sanitize(
            _git(root, "log", "-1", "--pretty=format:%an")
        ),
        "RING_GIT_AUTHOR_EMAIL": _git(
            root, "log", "-1", "--pretty=format:%ae"
        ),
        "RING_GIT_COMMITTED_AT": _git(
            root, "log", "-1", "--pretty=format:%cI"
        ),
        "RING_GIT_DIRTY": "1" if dirty else "0",
    }


def apply_git_build_args_to_environ(
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Populate missing RING_GIT_* env vars from the host checkout.

    Existing values are left alone so an explicit export still wins.
    """
    values = collect_host_git_build_args(repo_root)
    for key, value in values.items():
        os.environ.setdefault(key, value)
    return values
