"""Deploy history for `ring deploy history`.

Successful **Deploy ring-api** runs record a GitHub Deployment with
`environment=production-api` and `ref=<image sha>`. Older runs (before that
recording existed) fall back to parsing Actions logs for
`Deploy complete (<sha>)`.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from typing import Any

DEPLOY_WORKFLOW = "Deploy ring-api"
PRODUCTION_ENV = "production-api"  # distinct from Cloudflare "production"
COMPLETE_RE = re.compile(r"Deploy complete \(([0-9a-f]{7,40})\)")
TARGET_RE = re.compile(r"Deploy target ([0-9a-f]{7,40})")
RING_API_DESC_PREFIX = "ring-api "


@dataclass
class DeployRecord:
    sha: str
    short_sha: str
    when: str
    event: str
    conclusion: str
    source: str
    url: str | None = None
    run_id: int | None = None


def _gh_json(args: list[str]) -> Any:
    result = subprocess.run(
        ["gh", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def _short(sha: str) -> str:
    return sha[:7] if len(sha) >= 7 else sha


def deployments(limit: int) -> list[DeployRecord]:
    """List GitHub Deployments recorded by Deploy ring-api."""
    raw = _gh_json(
        [
            "api",
            f"repos/{{owner}}/{{repo}}/deployments"
            f"?environment={PRODUCTION_ENV}&per_page={limit}",
        ]
    )
    if not isinstance(raw, list):
        return []

    records: list[DeployRecord] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        sha = item.get("sha") or item.get("ref")
        if not isinstance(sha, str) or len(sha) < 7:
            continue
        desc = item.get("description") or ""
        payload = (
            item.get("payload")
            if isinstance(item.get("payload"), dict)
            else {}
        )
        workflow = (
            payload.get("workflow") if isinstance(payload, dict) else None
        )
        # Ignore stale Cloudflare / unrelated production deployments.
        if workflow != DEPLOY_WORKFLOW and not (
            isinstance(desc, str) and desc.startswith(RING_API_DESC_PREFIX)
        ):
            continue
        event = payload.get("event") if isinstance(payload, dict) else None
        records.append(
            DeployRecord(
                sha=sha,
                short_sha=_short(sha),
                when=str(item.get("created_at") or ""),
                event=str(event or item.get("task") or "deploy"),
                conclusion="success",
                source="github_deployment",
                url=item.get("url")
                if isinstance(item.get("url"), str)
                else None,
            )
        )
        if len(records) >= limit:
            break
    return records


def _sha_from_run_logs(run_id: int) -> tuple[str, str] | None:
    """Return (sha, source) from Actions logs, or None."""
    result = subprocess.run(
        ["gh", "run", "view", str(run_id), "--log"],
        check=False,
        text=True,
        capture_output=True,
    )
    text = (result.stdout or "") + (result.stderr or "")
    complete = COMPLETE_RE.search(text)
    if complete:
        return complete.group(1), "workflow_log_complete"
    target = TARGET_RE.search(text)
    if target:
        return target.group(1), "workflow_log_target"
    return None


def workflow_runs(limit: int, *, resolve_sha: bool) -> list[DeployRecord]:
    """Fall back to Deploy ring-api workflow runs (and optionally their logs)."""
    runs = _gh_json(
        [
            "run",
            "list",
            "--workflow",
            DEPLOY_WORKFLOW,
            "--limit",
            str(limit),
            "--json",
            "databaseId,conclusion,event,headSha,createdAt,url,displayTitle",
        ]
    )
    if not isinstance(runs, list):
        return []

    records: list[DeployRecord] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        run_id = run.get("databaseId")
        conclusion = str(run.get("conclusion") or "unknown")
        sha: str | None = None
        source = "workflow_run_head"
        if resolve_sha and isinstance(run_id, int):
            parsed = _sha_from_run_logs(run_id)
            if parsed:
                sha, source = parsed
        if not sha:
            head = run.get("headSha")
            sha = head if isinstance(head, str) else None
        if not sha:
            continue
        # Keep successful jobs. Also keep host-complete rollouts whose later
        # bookkeeping step failed (conclusion=failure but Deploy complete in
        # logs) — those are real prod deploys.
        if conclusion != "success" and source != "workflow_log_complete":
            continue
        records.append(
            DeployRecord(
                sha=sha,
                short_sha=_short(sha),
                when=str(run.get("createdAt") or ""),
                event=str(run.get("event") or ""),
                conclusion=conclusion,
                source=source,
                url=run.get("url")
                if isinstance(run.get("url"), str)
                else None,
                run_id=run_id if isinstance(run_id, int) else None,
            )
        )
    return records


def collect(
    limit: int = 20, *, resolve_logs: bool = False
) -> list[DeployRecord]:
    """Prefer GitHub Deployments; fill remaining slots from workflow runs."""
    records = deployments(limit)
    if len(records) >= limit:
        return records[:limit]

    seen = {r.sha for r in records}
    for run in workflow_runs(limit, resolve_sha=resolve_logs or not records):
        if run.sha in seen:
            continue
        records.append(run)
        seen.add(run.sha)
        if len(records) >= limit:
            break
    return records[:limit]


def format_record(record: DeployRecord) -> str:
    when = record.when.replace("T", " ").replace("Z", " UTC")
    bits = [
        record.short_sha,
        record.conclusion.ljust(8),
        record.event.ljust(16),
        when,
    ]
    if record.source == "workflow_run_head":
        bits.append(
            "(headSha — may differ from deployed image; use --resolve)"
        )
    elif (
        record.source == "workflow_log_complete"
        and record.conclusion != "success"
    ):
        bits.append("(host ok; Actions job failed after rollout)")
    return "  ".join(bits)


def as_dicts(records: list[DeployRecord]) -> list[dict[str, Any]]:
    return [asdict(r) for r in records]
