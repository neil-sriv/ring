"""Read what is actually deployed, for `ring deploy status`.

The frontend ships from Cloudflare Workers Builds and the API from a
SHA-tagged ECR image, so the two halves of prod move independently. Both
publish their commit: the frontend as a static `/version.json` written at
build time, the API as `GET /api/v1/version`.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dev_util.dev import ROOT_DIR

DEFAULT_BASE_URL = "https://ring.neilsriv.tech"
FRONTEND_VERSION_PATH = "/version.json"
API_VERSION_PATH = "/api/v1/version"
# Cloudflare answers the default Python-urllib User-Agent with 1010 / 403.
USER_AGENT = "ring-deploy-status/1.0"
REQUEST_TIMEOUT_SECONDS = 10.0
HTML_RESPONSE = "served HTML, not JSON"
NO_STAMP = "no /version.json — this deploy predates the build stamp"


@dataclass
class Component:
    """One deployed piece of prod, as it reports itself."""

    name: str
    sha: str | None = None
    branch: str | None = None
    timestamp: str | None = None
    timestamp_label: str = ""
    source: str | None = None
    detail: str | None = None
    error: str | None = None


def fetch_json(url: str, timeout: float = REQUEST_TIMEOUT_SECONDS) -> dict:
    """GET a URL and parse JSON, raising ValueError on anything else.

    The Worker serves index.html for unknown paths (SPA fallback), so a
    frontend without a build stamp returns HTML with a 200.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError(str(exc)) from exc
    if body.lstrip().startswith("<"):
        raise ValueError(HTML_RESPONSE)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"response was not JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError("response was not a JSON object")
    return payload


def parse_frontend(payload: dict) -> Component:
    """Read the build stamp emitted by react/plugins/version-stamp.ts."""
    source = payload.get("source")
    component = Component(
        name="frontend",
        sha=payload.get("sha"),
        branch=payload.get("branch"),
        timestamp=payload.get("built_at"),
        timestamp_label="built",
        source=source if isinstance(source, str) else None,
    )
    build_uuid = payload.get("build_uuid")
    if isinstance(build_uuid, str) and build_uuid:
        component.detail = f"build {build_uuid}"
    if component.sha is None:
        component.error = "build stamp has no commit"
    return component


def parse_api(payload: dict) -> Component:
    """Read image_build out of the API's /version response."""
    image = payload.get("image_build")
    if not isinstance(image, dict):
        return Component(name="api", error="/version has no image_build")
    component = Component(
        name="api",
        sha=image.get("sha"),
        branch=image.get("branch"),
        timestamp=image.get("committed_at"),
        timestamp_label="committed",
        source=image.get("source"),
        detail=image.get("subject"),
    )
    if component.sha is None:
        component.error = "API is running an image with no commit stamped"
    return component


def collect(base_url: str = DEFAULT_BASE_URL) -> list[Component]:
    """Probe both halves of prod, tolerating either being unreachable."""
    base = base_url.rstrip("/")
    components: list[Component] = []
    for name, path, parse in (
        ("frontend", FRONTEND_VERSION_PATH, parse_frontend),
        ("api", API_VERSION_PATH, parse_api),
    ):
        try:
            components.append(parse(fetch_json(f"{base}{path}")))
        except ValueError as exc:
            # The Worker's SPA fallback answers unknown paths with
            # index.html, so HTML here means the stamp is simply absent.
            missing = name == "frontend" and str(exc) == HTML_RESPONSE
            components.append(
                Component(name=name, error=NO_STAMP if missing else str(exc))
            )
    return components


def _git(
    *args: str, repo_root: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root or ROOT_DIR), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def commits_behind(sha: str, ref: str = "origin/dev") -> int | None:
    """Count commits on `ref` that `sha` does not have.

    Returns None when the commit or ref is missing from the local clone,
    which means a stale checkout rather than a bad deploy.
    """
    result = _git("rev-list", "--count", f"{sha}..{ref}")
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def age(timestamp: str | None, now: datetime | None = None) -> str | None:
    """Render an ISO-8601 timestamp as a compact age like `2h 5m ago`."""
    if not timestamp:
        return None
    text = timestamp.replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    reference = now or datetime.now(timezone.utc)
    seconds = int((reference - moment).total_seconds())
    if seconds < 0:
        return "in the future"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m ago"
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h ago"


def format_component(
    component: Component,
    behind: int | None = None,
    ref: str = "origin/dev",
) -> str:
    """Render one line of the human-readable status table."""
    if component.error and component.sha is None:
        return "  ".join([f"{component.name:<9}", "unknown", component.error])

    parts = [f"{component.name:<9}"]
    parts.append((component.sha or "")[:7] or "-------")
    parts.append(component.branch or "-")

    when = age(component.timestamp)
    if when:
        parts.append(f"{component.timestamp_label} {when}")
    elif component.timestamp:
        parts.append(f"{component.timestamp_label} {component.timestamp}")

    if behind == 0:
        parts.append(f"up to date with {ref}")
    elif behind is not None:
        plural = "" if behind == 1 else "s"
        parts.append(f"{behind} commit{plural} behind {ref}")

    if component.source:
        parts.append(f"via {component.source}")
    return "  ".join(parts)


def as_dict(component: Component, behind: int | None = None) -> dict:
    """Serialize one component for `--json`."""
    return {
        "name": component.name,
        "sha": component.sha,
        "branch": component.branch,
        "timestamp": component.timestamp,
        "timestamp_kind": component.timestamp_label or None,
        "age": age(component.timestamp),
        "commits_behind": behind,
        "source": component.source,
        "detail": component.detail,
        "error": component.error,
    }
