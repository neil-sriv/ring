"""Tests for version-info collection used by GET /version."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ring.fastapp.schemas.version import GitCommitInfo
from ring.lib.version_info import (
    clear_version_cache,
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
    def test_reads_host_snapshot(self, tmp_path: Path) -> None:
        snapshot = tmp_path / ".ring-runtime-version.json"
        snapshot.write_text(
            json.dumps(
                {
                    "generated_at": "2026-08-11T03:00:00+00:00",
                    "project": "ring",
                    "containers": [
                        {
                            "service": "api",
                            "name": "ring-api",
                            "container_id": "aaa",
                            "image": "prod-ring-api:latest",
                            "image_id": "sha256:apiimage",
                            "image_digest": (
                                "public.ecr.aws/z2k1e8p1/ring-api"
                                "@sha256:aaa111"
                            ),
                            "git_sha": "abc123",
                            "status": "running",
                            "state": "running",
                        },
                        {
                            "service": "frontend",
                            "name": "ring-frontend",
                            "container_id": "ccc",
                            "image": "prod-ring-frontend:latest",
                            "image_id": "sha256:feimage",
                            "image_digest": (
                                "public.ecr.aws/z2k1e8p1/"
                                "ring-frontend@sha256:bbb222"
                            ),
                            "git_sha": "abc123",
                            "status": "running",
                            "state": "running",
                        },
                    ],
                }
            )
        )
        info = collect_docker_info(snapshot_path=snapshot)
        assert info.available is True
        assert info.source == "snapshot"
        assert info.project == "ring"
        assert info.generated_at == "2026-08-11T03:00:00+00:00"
        assert [c.service for c in info.containers] == [
            "api",
            "frontend",
        ]
        assert info.containers[0].image_id == "sha256:apiimage"
        assert info.containers[0].image_digest == (
            "public.ecr.aws/z2k1e8p1/ring-api@sha256:aaa111"
        )
        assert info.containers[0].git_sha == "abc123"

    def test_snapshot_does_not_include_foreign_stacks(
        self, tmp_path: Path
    ) -> None:
        snapshot = tmp_path / ".ring-runtime-version.json"
        snapshot.write_text(
            json.dumps(
                {
                    "generated_at": "2026-08-11T03:00:00+00:00",
                    "project": "workspace",
                    "containers": [
                        {
                            "service": "api",
                            "name": "ring-api",
                            "container_id": "api1",
                            "image": "prod-ring-api",
                            "image_id": "sha256:api",
                            "image_digest": "prod-ring-api@sha256:abc",
                            "git_sha": None,
                            "status": "running",
                            "state": "running",
                        }
                    ],
                }
            )
        )
        info = collect_docker_info(snapshot_path=snapshot)
        assert info.available is True
        assert info.project == "workspace"
        assert len(info.containers) == 1
        assert info.containers[0].service == "api"
        assert info.containers[0].name == "ring-api"

    def test_missing_snapshot(self, tmp_path: Path) -> None:
        info = collect_docker_info(snapshot_path=tmp_path / "missing.json")
        assert info.available is False
        assert info.source == "unavailable"
        assert info.error is not None

    def test_invalid_snapshot(self, tmp_path: Path) -> None:
        snapshot = tmp_path / "bad.json"
        snapshot.write_text("not-json")
        info = collect_docker_info(snapshot_path=snapshot)
        assert info.available is False
        assert info.source == "unavailable"


class TestGetVersion:
    def test_combines_git_and_docker(self, tmp_path: Path) -> None:
        snapshot = tmp_path / "runtime.json"
        snapshot.write_text(
            json.dumps(
                {
                    "generated_at": "2026-08-11T03:00:00+00:00",
                    "project": "ring",
                    "containers": [],
                }
            )
        )
        version = get_version(
            environ={
                "RING_GIT_SHA": "checkoutsha",
                "RING_BUILD_GIT_SHA": "imagesha",
                "RING_BUILD_GIT_SUBJECT": "built",
            },
            hostname="ring-api",
            snapshot_path=snapshot,
        )
        assert version.hostname == "ring-api"
        assert version.git.sha == "checkoutsha"
        assert version.image_build.sha == "imagesha"
        assert version.image_build.subject == "built"
        assert version.docker.available is True
        assert version.docker.source == "snapshot"
        assert version.docker.containers == []

    def test_caches_unparameterized_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        clear_version_cache()
        calls = {"n": 0}

        def counting_git(*args: object, **kwargs: object) -> GitCommitInfo:
            calls["n"] += 1
            return GitCommitInfo(sha="cached", source="env")

        monkeypatch.setattr(
            "ring.lib.version_info.collect_checkout_git",
            counting_git,
        )
        first = get_version()
        second = get_version()
        assert calls["n"] == 1
        assert first is second
        clear_version_cache()
        get_version()
        assert calls["n"] == 2
        clear_version_cache()

    def test_cache_expires(self, monkeypatch: pytest.MonkeyPatch) -> None:
        clear_version_cache()
        clock = {"t": 100.0}
        monkeypatch.setattr(
            "ring.lib.version_info.time.monotonic",
            lambda: clock["t"],
        )
        calls = {"n": 0}

        def counting_git(*args: object, **kwargs: object) -> GitCommitInfo:
            calls["n"] += 1
            return GitCommitInfo(sha=f"n{calls['n']}", source="env")

        monkeypatch.setattr(
            "ring.lib.version_info.collect_checkout_git",
            counting_git,
        )
        get_version()
        clock["t"] += 14
        get_version()
        assert calls["n"] == 1
        clock["t"] += 2
        get_version()
        assert calls["n"] == 2
        clear_version_cache()


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
