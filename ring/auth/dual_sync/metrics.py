"""In-process counters for dual-write success rate and dual-read drift."""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class DualSyncSnapshot:
    """Point-in-time dual-sync counters for logs and the admin endpoint."""

    write_attempts: int
    write_successes: int
    write_failures: int
    write_skipped: int
    read_attempts: int
    read_matches: int
    read_missing: int
    read_mismatches: int
    read_failures: int

    @property
    def write_success_rate(self) -> float | None:
        if self.write_attempts == 0:
            return None
        return self.write_successes / self.write_attempts

    @property
    def drift_count(self) -> int:
        return self.read_missing + self.read_mismatches


class DualSyncMetrics:
    """Thread-safe counters. Process-local; reset on restart."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._write_attempts = 0
        self._write_successes = 0
        self._write_failures = 0
        self._write_skipped = 0
        self._read_attempts = 0
        self._read_matches = 0
        self._read_missing = 0
        self._read_mismatches = 0
        self._read_failures = 0

    def record_write_success(self) -> None:
        with self._lock:
            self._write_attempts += 1
            self._write_successes += 1

    def record_write_failure(self) -> None:
        with self._lock:
            self._write_attempts += 1
            self._write_failures += 1

    def record_write_skipped(self) -> None:
        with self._lock:
            self._write_skipped += 1

    def record_read_match(self) -> None:
        with self._lock:
            self._read_attempts += 1
            self._read_matches += 1

    def record_read_missing(self) -> None:
        with self._lock:
            self._read_attempts += 1
            self._read_missing += 1

    def record_read_mismatch(self) -> None:
        with self._lock:
            self._read_attempts += 1
            self._read_mismatches += 1

    def record_read_failure(self) -> None:
        with self._lock:
            self._read_attempts += 1
            self._read_failures += 1

    def snapshot(self) -> DualSyncSnapshot:
        with self._lock:
            return DualSyncSnapshot(
                write_attempts=self._write_attempts,
                write_successes=self._write_successes,
                write_failures=self._write_failures,
                write_skipped=self._write_skipped,
                read_attempts=self._read_attempts,
                read_matches=self._read_matches,
                read_missing=self._read_missing,
                read_mismatches=self._read_mismatches,
                read_failures=self._read_failures,
            )

    def reset(self) -> None:
        with self._lock:
            self._write_attempts = 0
            self._write_successes = 0
            self._write_failures = 0
            self._write_skipped = 0
            self._read_attempts = 0
            self._read_matches = 0
            self._read_missing = 0
            self._read_mismatches = 0
            self._read_failures = 0


metrics = DualSyncMetrics()
