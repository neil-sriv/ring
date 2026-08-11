"""Pydantic schemas for the public /version endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GitCommitInfo(BaseModel):
    """Git commit metadata from a live checkout or a baked image."""

    sha: str | None = None
    short_sha: str | None = None
    branch: str | None = None
    subject: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    committed_at: str | None = None
    dirty: bool | None = None
    source: Literal["git", "env", "image_env", "unavailable"] = "unavailable"


class ContainerVersion(BaseModel):
    """Identity of a running (or recently stopped) compose container."""

    service: str | None = None
    name: str
    container_id: str
    image: str | None = None
    image_id: str | None = Field(
        default=None,
        description="Local image id, typically sha256:<digest>",
    )
    image_digest: str | None = Field(
        default=None,
        description="Registry digest (name@sha256:...) when the image was pulled",
    )
    git_sha: str | None = Field(
        default=None,
        description="org.opencontainers.image.revision label baked into the image",
    )
    status: str | None = None
    state: str | None = None


class DockerInfo(BaseModel):
    """Docker Engine view of this compose project's containers."""

    available: bool
    error: str | None = None
    socket_path: str | None = None
    project: str | None = None
    containers: list[ContainerVersion] = Field(default_factory=list)


class VersionResponse(BaseModel):
    """Deploy diagnostic payload for GET /version."""

    hostname: str
    git: GitCommitInfo
    image_build: GitCommitInfo
    docker: DockerInfo
