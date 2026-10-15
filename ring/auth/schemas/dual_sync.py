"""Response schema for dual-sync visibility."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DualSyncStats(BaseModel):
    """In-process dual-write / dual-read counters. Resets on process restart."""

    dual_write_enabled: bool
    dual_read_enabled: bool
    identity_configured: bool
    write_attempts: int
    write_successes: int
    write_failures: int
    write_skipped: int
    write_success_rate: float | None = Field(
        default=None,
        description="write_successes / write_attempts, or null if no attempts",
    )
    read_attempts: int
    read_matches: int
    read_missing: int
    read_mismatches: int
    read_failures: int
    drift_count: int = Field(
        description="Identity missing + field mismatches",
    )
