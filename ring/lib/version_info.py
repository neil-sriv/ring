"""Collect git and Docker identity for the public /version endpoint."""

from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from ring.fastapp.schemas.version import (
    ContainerVersion,
    DockerInfo,
    GitCommitInfo,
    VersionResponse,
)

DOCKER_API_PREFIX = "/v1.41"
DEFAULT_DOCKER_SOCKET = "/var/run/docker.sock"
GIT_DIR_CANDIDATES = ("/git", "/src/.git")
RING_COMPOSE_PROJECTS = frozenset({"ring"})
RING_SERVICE_NAMES = frozenset(
    {
        "api",
        "nginx",
        "frontend",
        "certbot",
        "cockroach",
        "llm",
        "test-cockroach",
        "test-runner",
    }
)
GIT_DISCOVERY_ROOTS = (Path.cwd(), Path("/workspace"), Path("/src"))

JsonGetter = Callable[[str], Any]
GitSource = Literal["git", "env", "image_env", "unavailable"]


class UnixHTTPConnection(http.client.HTTPConnection):
    """HTTP client that talks to a Unix domain socket."""

    def __init__(self, socket_path: str, timeout: float = 2.0) -> None:
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.socket_path)
        self.sock = sock


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


def resolve_docker_socket_path(
    environ: dict[str, str] | None = None,
) -> str | None:
    docker_host = _env("DOCKER_HOST", environ)
    if docker_host:
        if docker_host.startswith("unix://"):
            return docker_host.removeprefix("unix://")
        return None
    if Path(DEFAULT_DOCKER_SOCKET).exists():
        return DEFAULT_DOCKER_SOCKET
    return None


def docker_get_json(socket_path: str, path: str) -> Any:
    connection = UnixHTTPConnection(socket_path)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        if response.status >= 400:
            raise RuntimeError(
                f"Docker API {path} returned {response.status}: "
                f"{body[:200]!r}"
            )
        if not body:
            return None
        return json.loads(body)
    finally:
        connection.close()


def _container_name(raw: dict[str, Any]) -> str:
    names = raw.get("Names") or []
    if names:
        return str(names[0]).lstrip("/")
    return str(raw.get("Id", ""))[:12]


def _is_ring_container(raw: dict[str, Any], project: str | None) -> bool:
    labels = raw.get("Labels") or {}
    compose_project = labels.get("com.docker.compose.project")
    service = labels.get("com.docker.compose.service")
    name = _container_name(raw)
    if project:
        return compose_project == project
    if compose_project in RING_COMPOSE_PROJECTS:
        return True
    if service in RING_SERVICE_NAMES:
        return True
    return name.startswith("ring-")


def _inspect_self_project(
    request_json: JsonGetter,
    hostname: str,
) -> str | None:
    try:
        inspected = request_json(
            f"{DOCKER_API_PREFIX}/containers/{quote(hostname, safe='')}/json"
        )
    except Exception:
        return None
    if not isinstance(inspected, dict):
        return None
    labels = (inspected.get("Config") or {}).get("Labels") or {}
    project = labels.get("com.docker.compose.project")
    return str(project) if project else None


def _image_revision_and_digest(
    request_json: JsonGetter, image_id: str | None
) -> tuple[str | None, str | None]:
    if not image_id:
        return None, None
    try:
        inspected = request_json(
            f"{DOCKER_API_PREFIX}/images/{quote(image_id, safe='')}/json"
        )
    except Exception:
        return None, None
    if not isinstance(inspected, dict):
        return None, None
    labels = (inspected.get("Config") or {}).get("Labels") or {}
    revision = labels.get("org.opencontainers.image.revision") or None
    digests = inspected.get("RepoDigests") or []
    digest = str(digests[0]) if digests else None
    return revision, digest


def collect_docker_info(
    *,
    environ: dict[str, str] | None = None,
    hostname: str | None = None,
    request_json: JsonGetter | None = None,
    socket_path: str | None = None,
) -> DockerInfo:
    resolved_socket = socket_path or resolve_docker_socket_path(environ)
    getter = request_json
    if getter is None:
        if resolved_socket is None:
            return DockerInfo(
                available=False,
                error="Docker socket not found",
                socket_path=None,
            )

        def getter(path: str) -> Any:
            return docker_get_json(resolved_socket, path)

    host = hostname or socket.gethostname()
    try:
        project = _inspect_self_project(getter, host)
        listed = getter(f"{DOCKER_API_PREFIX}/containers/json?all=true")
    except Exception as exc:
        return DockerInfo(
            available=False,
            error=str(exc),
            socket_path=resolved_socket,
        )

    if not isinstance(listed, list):
        return DockerInfo(
            available=False,
            error="Docker API returned a non-list container payload",
            socket_path=resolved_socket,
            project=project,
        )

    containers: list[ContainerVersion] = []
    for raw in listed:
        if not isinstance(raw, dict):
            continue
        if not _is_ring_container(raw, project):
            continue
        image_id = raw.get("ImageID")
        git_sha, image_digest = _image_revision_and_digest(getter, image_id)
        labels = raw.get("Labels") or {}
        containers.append(
            ContainerVersion(
                service=labels.get("com.docker.compose.service"),
                name=_container_name(raw),
                container_id=str(raw.get("Id", "")),
                image=raw.get("Image"),
                image_id=image_id,
                image_digest=image_digest,
                git_sha=git_sha,
                status=raw.get("Status"),
                state=raw.get("State"),
            )
        )
    containers.sort(key=lambda item: (item.service or "", item.name))
    return DockerInfo(
        available=True,
        error=None,
        socket_path=resolved_socket,
        project=project,
        containers=containers,
    )


def get_version(
    *,
    environ: dict[str, str] | None = None,
    hostname: str | None = None,
    request_json: JsonGetter | None = None,
    socket_path: str | None = None,
    git_dir: Path | None = None,
) -> VersionResponse:
    return VersionResponse(
        hostname=hostname or socket.gethostname(),
        git=collect_checkout_git(environ, git_dir=git_dir),
        image_build=collect_image_build_git(environ),
        docker=collect_docker_info(
            environ=environ,
            hostname=hostname,
            request_json=request_json,
            socket_path=socket_path,
        ),
    )
