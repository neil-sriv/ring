"""Tests for version-info collection used by GET /version."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from ring.lib.version_info import (
    collect_checkout_git,
    collect_docker_info,
    collect_image_build_git,
    get_version,
)


class TestGitCollection:
    def test_env_prefix_round_trip(self) -> None:
        info = collect_checkout_git(
            {
                "RING_GIT_SHA": "abc123def456",
                "RING_GIT_BRANCH": "dev",
                "RING_GIT_SUBJECT": "fix due date",
                "RING_GIT_AUTHOR_NAME": "Neil",
                "RING_GIT_AUTHOR_EMAIL": "neil@example.com",
                "RING_GIT_COMMITTED_AT": "2026-08-11T00:00:00Z",
                "RING_GIT_DIRTY": "0",
            }
        )
        assert info.source == "env"
        assert info.sha == "abc123def456"
        assert info.short_sha == "abc123d"
        assert info.branch == "dev"
        assert info.subject == "fix due date"
        assert info.author_name == "Neil"
        assert info.dirty is False

    def test_image_build_env(self) -> None:
        info = collect_image_build_git(
            {
                "RING_BUILD_GIT_SHA": "deadbeefcafebabe",
                "RING_BUILD_GIT_SUBJECT": "bake me",
            }
        )
        assert info.source == "image_env"
        assert info.sha == "deadbeefcafebabe"
        assert info.subject == "bake me"

    def test_unavailable_when_empty(self) -> None:
        assert collect_checkout_git({}).source == "unavailable"
        assert collect_image_build_git({}).source == "unavailable"

    def test_reads_real_git_dir(self, tmp_path: Path) -> None:
        if not _git_available():
            pytest.skip("git is not installed")
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "dev@example.com")
        _git(repo, "config", "user.name", "Dev")
        (repo / "README").write_text("hi\n")
        _git(repo, "add", "README")
        _git(repo, "commit", "-m", "initial commit")
        sha = _git(repo, "rev-parse", "HEAD")
        info = collect_checkout_git(git_dir=repo / ".git")
        assert info.source == "git"
        assert info.sha == sha
        assert info.subject == "initial commit"
        assert info.author_email == "dev@example.com"


class TestDockerCollection:
    def test_filters_to_compose_project(self) -> None:
        payloads = {
            "/v1.41/containers/ring-api/json": {
                "Config": {"Labels": {"com.docker.compose.project": "ring"}}
            },
            "/v1.41/containers/json?all=true": [
                {
                    "Id": "aaa",
                    "Names": ["/ring-api"],
                    "Image": "prod-ring-api:latest",
                    "ImageID": "sha256:apiimage",
                    "State": "running",
                    "Status": "Up 2 hours",
                    "Labels": {
                        "com.docker.compose.project": "ring",
                        "com.docker.compose.service": "api",
                    },
                },
                {
                    "Id": "bbb",
                    "Names": ["/unrelated"],
                    "Image": "nginx:latest",
                    "ImageID": "sha256:other",
                    "State": "running",
                    "Status": "Up 1 hour",
                    "Labels": {
                        "com.docker.compose.project": "otherapp",
                        "com.docker.compose.service": "web",
                    },
                },
                {
                    "Id": "ccc",
                    "Names": ["/ring-frontend"],
                    "Image": "prod-ring-frontend:latest",
                    "ImageID": "sha256:feimage",
                    "State": "running",
                    "Status": "Up 2 hours",
                    "Labels": {
                        "com.docker.compose.project": "ring",
                        "com.docker.compose.service": "frontend",
                    },
                },
            ],
            "/v1.41/images/sha256%3Aapiimage/json": {
                "Config": {
                    "Labels": {"org.opencontainers.image.revision": "abc123"}
                },
                "RepoDigests": [
                    "public.ecr.aws/z2k1e8p1/ring-api@sha256:aaa111"
                ],
            },
            "/v1.41/images/sha256%3Afeimage/json": {
                "Config": {
                    "Labels": {"org.opencontainers.image.revision": "abc123"}
                },
                "RepoDigests": [
                    "public.ecr.aws/z2k1e8p1/ring-frontend@sha256:bbb222"
                ],
            },
        }

        def request_json(path: str) -> Any:
            return payloads[path]

        info = collect_docker_info(
            hostname="ring-api",
            request_json=request_json,
            socket_path="/var/run/docker.sock",
        )
        assert info.available is True
        assert info.project == "ring"
        assert [c.service for c in info.containers] == ["api", "frontend"]
        assert info.containers[0].image_id == "sha256:apiimage"
        assert (
            info.containers[0].image_digest
            == "public.ecr.aws/z2k1e8p1/ring-api@sha256:aaa111"
        )
        assert info.containers[0].git_sha == "abc123"

    def test_includes_known_services_without_project(self) -> None:
        def request_json(path: str) -> Any:
            if path.endswith("/containers/unknown-host/json"):
                raise RuntimeError("no such container")
            if path.startswith("/v1.41/containers/json"):
                return [
                    {
                        "Id": "api1",
                        "Names": ["/whatever-api-1"],
                        "Image": "prod-ring-api",
                        "ImageID": "sha256:api",
                        "State": "running",
                        "Status": "Up",
                        "Labels": {
                            "com.docker.compose.project": "workspace",
                            "com.docker.compose.service": "api",
                        },
                    }
                ]
            return {
                "Config": {"Labels": {}},
                "RepoDigests": ["prod-ring-api@sha256:abc"],
            }

        info = collect_docker_info(
            hostname="unknown-host",
            request_json=request_json,
            socket_path="/var/run/docker.sock",
        )
        assert info.available is True
        assert info.project is None
        assert len(info.containers) == 1
        assert info.containers[0].service == "api"
        assert info.containers[0].image_digest == "prod-ring-api@sha256:abc"

    def test_missing_socket(self, tmp_path: Path) -> None:
        info = collect_docker_info(
            environ={"DOCKER_HOST": "unix://" + str(tmp_path / "missing.sock")}
        )
        assert info.available is False
        assert info.error is not None


class TestGetVersion:
    def test_combines_git_and_docker(self) -> None:
        version = get_version(
            environ={
                "RING_GIT_SHA": "checkoutsha",
                "RING_BUILD_GIT_SHA": "imagesha",
                "RING_BUILD_GIT_SUBJECT": "built",
            },
            hostname="ring-api",
            request_json=lambda path: (
                {"Config": {"Labels": {"com.docker.compose.project": "ring"}}}
                if path.endswith("/json") and "containers/ring-api" in path
                else []
                if path.startswith("/v1.41/containers/json")
                else {}
            ),
            socket_path="/var/run/docker.sock",
        )
        assert version.hostname == "ring-api"
        assert version.git.sha == "checkoutsha"
        assert version.image_build.sha == "imagesha"
        assert version.image_build.subject == "built"
        assert version.docker.available is True
        assert version.docker.containers == []


def _git_available() -> bool:
    try:
        subprocess.run(
            ["git", "--version"],
            check=True,
            capture_output=True,
            timeout=2,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
