"""Collect git and host-snapshot identity for the public /version endpoint."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Literal

from ring.fastapp.schemas.version import (
    ContainerVersion,
    DockerInfo,
    GitCommitInfo,
    VersionResponse,
)

DEFAULT_SNAPSHOT_PATH = Path("/var/ring/runtime-version.json")
HOST_SNAPSHOT_NAME = ".ring-runtime-version.json"
GIT_DIR_CANDIDATES = ("/git", "/src/.git")
GIT_DISCOVERY_ROOTS = (Path.cwd(), Path("/workspace"), Path("/src"))
VERSION_CACHE_TTL_SECONDS = 15.0

GitSource = Literal["git", "env", "image_env", "unavailable"]

_cache_lock = threading.Lock()
_cached_at: float | None = None
_cached_version: VersionResponse | None = None


def _env(name: str, environ: dict[str, str] | None = None) -> str | None:
    value = (environ if environ is not None else os.environ).get(name, "")
    value = value.strip()
    return value or None


def _prefix_env(
    prefix: str, environ: dict[str, str] | None = None
) -> dict[str, str | None]:
    return {
        "sha": _env(f"{prefix}SHA", environ),
        "short_sha": _env(f"{prefix}SHORT_SHA", environ),
        "branch": _env(f"{prefix}BRANCH", environ),
        "subject": _env(f"{prefix}SUBJECT", environ),
        "author_name": _env(f"{prefix}AUTHOR_NAME", environ),
        "author_email": _env(f"{prefix}AUTHOR_EMAIL", environ),
        "committed_at": _env(f"{prefix}COMMITTED_AT", environ),
        "dirty_raw": _env(f"{prefix}DIRTY", environ),
    }


def _git_info_from_prefixed_env(
    prefix: str,
    source: GitSource,
    environ: dict[str, str] | None = None,
) -> GitCommitInfo:
    values = _prefix_env(prefix, environ)
    dirty_raw = values.pop("dirty_raw")
    dirty: bool | None = None
    if dirty_raw is not None:
        dirty = dirty_raw in {"1", "true", "True", "yes"}
    if not any(values.values()) and dirty is None:
        return GitCommitInfo(source="unavailable")
    short_sha = values["short_sha"]
    if short_sha is None and values["sha"]:
        short_sha = values["sha"][:7]
    return GitCommitInfo(
        sha=values["sha"],
        short_sha=short_sha,
        branch=values["branch"],
        subject=values["subject"],
        author_name=values["author_name"],
        author_email=values["author_email"],
        committed_at=values["committed_at"],
        dirty=dirty,
        source=source,
    )


def _run_git(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def _git_dir_candidates(
    environ: dict[str, str] | None = None,
    extra: Path | None = None,
) -> list[Path]:
    paths: list[Path] = []
    configured = _env("RING_GIT_DIR", environ)
    if configured:
        paths.append(Path(configured))
    if extra is not None:
        paths.append(extra)
    paths.extend(Path(candidate) for candidate in GIT_DIR_CANDIDATES)
    return paths


def collect_git_from_dir(
    git_dir: Path,
    work_tree: Path | None = None,
) -> GitCommitInfo | None:
    """Read commit metadata from a .git directory via the git CLI."""
    if not git_dir.is_dir():
        return None
    git_args = ["--git-dir", str(git_dir)]
    if work_tree is not None and work_tree.is_dir():
        git_args.extend(["--work-tree", str(work_tree)])
    sha = _run_git([*git_args, "rev-parse", "HEAD"])
    if sha is None:
        return None
    short_sha = _run_git([*git_args, "rev-parse", "--short", "HEAD"])
    branch = _run_git([*git_args, "rev-parse", "--abbrev-ref", "HEAD"])
    subject = _run_git([*git_args, "log", "-1", "--pretty=format:%s"])
    author_name = _run_git([*git_args, "log", "-1", "--pretty=format:%an"])
    author_email = _run_git([*git_args, "log", "-1", "--pretty=format:%ae"])
    committed_at = _run_git([*git_args, "log", "-1", "--pretty=format:%cI"])
    dirty: bool | None = None
    if work_tree is not None and work_tree.is_dir():
        porcelain = _run_git([*git_args, "status", "--porcelain"])
        if porcelain is not None:
            dirty = bool(porcelain)
    return GitCommitInfo(
        sha=sha,
        short_sha=short_sha or sha[:7],
        branch=branch,
        subject=subject,
        author_name=author_name,
        author_email=author_email,
        committed_at=committed_at,
        dirty=dirty,
        source="git",
    )


def _discover_git_from_work_trees() -> GitCommitInfo | None:
    for root in GIT_DISCOVERY_ROOTS:
        if not root.is_dir():
            continue
        absolute_git_dir = _run_git(
            ["-C", str(root), "rev-parse", "--absolute-git-dir"]
        )
        if not absolute_git_dir:
            continue
        info = collect_git_from_dir(Path(absolute_git_dir), work_tree=root)
        if info is not None:
            return info
    return None


def collect_checkout_git(
    environ: dict[str, str] | None = None,
    git_dir: Path | None = None,
) -> GitCommitInfo:
    for candidate in _git_dir_candidates(environ, extra=git_dir):
        info = collect_git_from_dir(candidate)
        if info is not None:
            return info
    if environ is None:
        discovered = _discover_git_from_work_trees()
        if discovered is not None:
            return discovered
    env_info = _git_info_from_prefixed_env("RING_GIT_", "env", environ)
    if env_info.source != "unavailable":
        return env_info
    return GitCommitInfo(source="unavailable")


def collect_image_build_git(
    environ: dict[str, str] | None = None,
) -> GitCommitInfo:
    return _git_info_from_prefixed_env("RING_BUILD_GIT_", "image_env", environ)


def resolve_snapshot_path(
    environ: dict[str, str] | None = None,
    snapshot_path: Path | str | None = None,
) -> Path:
    if snapshot_path is not None:
        return Path(snapshot_path)
    configured = _env("RING_RUNTIME_VERSION_PATH", environ)
    if configured:
        return Path(configured)
    if DEFAULT_SNAPSHOT_PATH.is_file():
        return DEFAULT_SNAPSHOT_PATH
    for root in GIT_DISCOVERY_ROOTS:
        for candidate in (
            root / HOST_SNAPSHOT_NAME,
            root.parent / HOST_SNAPSHOT_NAME,
        ):
            if candidate.is_file():
                return candidate
    return DEFAULT_SNAPSHOT_PATH


def _container_from_raw(raw: dict[str, Any]) -> ContainerVersion:
    name = str(raw.get("name") or raw.get("container_id") or "")
    return ContainerVersion(
        service=raw.get("service"),
        name=name,
        container_id=str(raw.get("container_id") or ""),
        image=raw.get("image"),
        image_id=raw.get("image_id"),
        image_digest=raw.get("image_digest"),
        git_sha=raw.get("git_sha"),
        status=raw.get("status"),
        state=raw.get("state"),
    )


def collect_docker_info(
    *,
    environ: dict[str, str] | None = None,
    snapshot_path: Path | str | None = None,
) -> DockerInfo:
    path = resolve_snapshot_path(environ, snapshot_path)
    if not path.is_file():
        return DockerInfo(
            available=False,
            error="Runtime version snapshot not found",
            source="unavailable",
            snapshot_path=str(path),
        )
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return DockerInfo(
            available=False,
            error=str(exc),
            source="unavailable",
            snapshot_path=str(path),
        )
    if not isinstance(payload, dict):
        return DockerInfo(
            available=False,
            error="Runtime version snapshot is not an object",
            source="unavailable",
            snapshot_path=str(path),
        )

    raw_containers = payload.get("containers") or []
    containers: list[ContainerVersion] = []
    if isinstance(raw_containers, list):
        for raw in raw_containers:
            if isinstance(raw, dict):
                containers.append(_container_from_raw(raw))
    containers.sort(key=lambda item: (item.service or "", item.name))
    error = payload.get("error")
    return DockerInfo(
        available=error is None,
        error=str(error) if error is not None else None,
        source="snapshot",
        snapshot_path=str(path),
        generated_at=payload.get("generated_at"),
        project=payload.get("project"),
        containers=containers,
    )


def clear_version_cache() -> None:
    global _cached_at, _cached_version
    with _cache_lock:
        _cached_at = None
        _cached_version = None


def _should_use_cache(
    *,
    environ: dict[str, str] | None,
    hostname: str | None,
    snapshot_path: Path | str | None,
    git_dir: Path | None,
    use_cache: bool | None,
) -> bool:
    if use_cache is not None:
        return use_cache
    return (
        environ is None
        and hostname is None
        and snapshot_path is None
        and git_dir is None
    )


def get_version(
    *,
    environ: dict[str, str] | None = None,
    hostname: str | None = None,
    snapshot_path: Path | str | None = None,
    git_dir: Path | None = None,
    use_cache: bool | None = None,
) -> VersionResponse:
    global _cached_at, _cached_version
    use_cached = _should_use_cache(
        environ=environ,
        hostname=hostname,
        snapshot_path=snapshot_path,
        git_dir=git_dir,
        use_cache=use_cache,
    )
    now = time.monotonic()
    if use_cached:
        with _cache_lock:
            if (
                _cached_version is not None
                and _cached_at is not None
                and now - _cached_at < VERSION_CACHE_TTL_SECONDS
            ):
                return _cached_version

    payload = VersionResponse(
        hostname=hostname or socket.gethostname(),
        git=collect_checkout_git(environ, git_dir=git_dir),
        image_build=collect_image_build_git(environ),
        docker=collect_docker_info(
            environ=environ,
            snapshot_path=snapshot_path,
        ),
    )
    if use_cached:
        with _cache_lock:
            _cached_at = time.monotonic()
            _cached_version = payload
    return payload
