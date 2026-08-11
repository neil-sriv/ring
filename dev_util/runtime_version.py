"""Write a host-side Docker identity snapshot for GET /version.

The API never talks to the Docker Engine. `ring compose` and `prod.sh`
inspect containers/images on the host and write `.ring-runtime-version.json`,
which compose mounts read-only into the API.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
SNAPSHOT_NAME = ".ring-runtime-version.json"
PLACEHOLDER = {
    "generated_at": None,
    "project": None,
    "containers": [],
}
KNOWN_CONTAINER_NAMES = (
    "ring-api",
    "ring-nginx",
    "ring-frontend",
    "ring-cockroach",
    "ring-llm",
    "certbot",
)


def snapshot_path(repo_root: Path | None = None) -> Path:
    return (repo_root or ROOT_DIR) / SNAPSHOT_NAME


def ensure_snapshot_file(path: Path | None = None) -> Path:
    """Create the snapshot file so Compose bind-mounts a file, not a dir."""
    target = path or snapshot_path()
    if target.is_dir():
        shutil.rmtree(target)
    if not target.is_file():
        target.write_text(json.dumps(PLACEHOLDER) + "\n")
    return target


def _docker_prefix() -> list[str]:
    return shlex.split(os.environ.get("RING_DOCKER", "docker"))


def _docker_json(args: list[str]) -> Any | None:
    try:
        result = subprocess.run(
            [*_docker_prefix(), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _inspect(ref: str) -> dict[str, Any] | None:
    payload = _docker_json(["inspect", ref])
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    if isinstance(payload, dict):
        return payload
    return None


def _service_from_image_ref(ref: str) -> str | None:
    name = ref.rsplit("/", 1)[-1].split(":", 1)[0]
    for prefix in ("prod-ring-", "ring-"):
        if name.startswith(prefix):
            return name.removeprefix(prefix)
    return name or None


def _image_digest_and_git(
    image_id: str | None,
) -> tuple[str | None, str | None]:
    if not image_id:
        return None, None
    inspected = _inspect(image_id)
    if inspected is None:
        return None, None
    labels = (inspected.get("Config") or {}).get("Labels") or {}
    git_sha = labels.get("org.opencontainers.image.revision") or None
    digests = inspected.get("RepoDigests") or []
    digest = str(digests[0]) if digests else None
    return digest, git_sha


def _container_record(inspected: dict[str, Any]) -> dict[str, Any]:
    labels = (inspected.get("Config") or {}).get("Labels") or {}
    state = inspected.get("State") or {}
    image_id = inspected.get("Image")
    digest, git_sha = _image_digest_and_git(
        str(image_id) if image_id else None
    )
    if git_sha is None:
        git_sha = labels.get("org.opencontainers.image.revision") or None
    return {
        "service": labels.get("com.docker.compose.service"),
        "name": str(inspected.get("Name") or "").lstrip("/")
        or str(inspected.get("Id", ""))[:12],
        "container_id": str(inspected.get("Id") or ""),
        "image": (inspected.get("Config") or {}).get("Image"),
        "image_id": image_id,
        "image_digest": digest,
        "git_sha": git_sha,
        "status": state.get("Status"),
        "state": "running" if state.get("Running") else state.get("Status"),
        "project": labels.get("com.docker.compose.project"),
    }


def _image_record(ref: str, inspected: dict[str, Any]) -> dict[str, Any]:
    labels = (inspected.get("Config") or {}).get("Labels") or {}
    digests = inspected.get("RepoDigests") or []
    tags = inspected.get("RepoTags") or []
    return {
        "service": _service_from_image_ref(ref),
        "name": ref,
        "container_id": "",
        "image": tags[0] if tags else ref,
        "image_id": inspected.get("Id"),
        "image_digest": str(digests[0]) if digests else None,
        "git_sha": labels.get("org.opencontainers.image.revision") or None,
        "status": None,
        "state": "image",
    }


def collect_runtime_snapshot(
    *,
    extra_images: list[str] | None = None,
) -> dict[str, Any]:
    containers: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    project: str | None = None
    error: str | None = None

    for name in KNOWN_CONTAINER_NAMES:
        inspected = _inspect(name)
        if inspected is None:
            continue
        if "State" not in inspected and "RepoTags" in inspected:
            continue
        record = _container_record(inspected)
        cid = record["container_id"]
        if cid and cid in seen_ids:
            continue
        if cid:
            seen_ids.add(cid)
        project = project or record.pop("project", None)
        record.pop("project", None)
        containers.append(record)

    for ref in extra_images or []:
        ref = ref.strip()
        if not ref:
            continue
        inspected = _inspect(ref)
        if inspected is None:
            continue
        if "State" in inspected and inspected.get("Id") in seen_ids:
            continue
        if containers and any(
            item.get("image") == ref or item.get("name") == ref
            for item in containers
        ):
            continue
        containers.append(_image_record(ref, inspected))

    if not containers and extra_images:
        if _inspect(extra_images[0]) is None:
            error = "docker inspect returned no matching images"

    generated_at = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "project": project,
        "containers": containers,
    }
    if error:
        payload["error"] = error
    return payload


def write_snapshot(
    *,
    output: Path | None = None,
    extra_images: list[str] | None = None,
    repo_root: Path | None = None,
) -> Path:
    target = output or snapshot_path(repo_root)
    ensure_snapshot_file(target)
    payload = collect_runtime_snapshot(extra_images=extra_images)
    target.write_text(json.dumps(payload, indent=2) + "\n")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write .ring-runtime-version.json from host docker inspect."
        )
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="write",
        choices=("write",),
    )
    parser.add_argument(
        "--images",
        default="",
        help="Comma-separated image refs when containers are not running",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    images = [part for part in args.images.split(",") if part.strip()]
    try:
        path = write_snapshot(output=args.output, extra_images=images)
    except Exception as exc:
        print(f"runtime version snapshot failed: {exc}", file=sys.stderr)
        return 0
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
