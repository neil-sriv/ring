"""Compare `ring/db/schema.sql` against a database built from migrations.

pytest builds its schema from `schema.sql` while production is built by
alembic, so the two can disagree without any existing check noticing. That
matters most for tables and columns: a migration that adds a column without
`ring db autogenerate-schema` leaves the suite testing a schema prod does
not have.

Only table and column *names* are compared. Column defaults, index ordering
and sequences already diverge (migrations emit `unique_rowid()`, the
committed dump still carries `nextval(...)` sequences), and reconciling that
is a separate change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# APScheduler creates its own table at runtime; no migration owns it.
UNMIGRATED_TABLES = frozenset({"public.apscheduler_jobs"})

_TABLE_RE = re.compile(r"CREATE TABLE ([^\s(]+) \((.*?)\n\);", re.S)
_NON_COLUMN_PREFIXES = (
    "CONSTRAINT",
    "INDEX",
    "UNIQUE INDEX",
    "VECTOR INDEX",
    "INVERTED INDEX",
    "FAMILY",
)


def clean_dump(raw: str) -> str:
    """Turn `SHOW CREATE ALL TABLES` output into plain SQL.

    The CLI quotes every statement and doubles interior quotes, so unwrap via
    a placeholder the same way `ring db autogenerate-schema` does.
    """
    cleaned = raw.replace('""', "%").replace('"', "").replace("%", '"')
    lines = cleaned.split("\n")
    if lines and "create_statement" in lines[0]:
        lines = lines[1:]
    return "\n".join(lines)


def parse_tables(sql: str) -> dict[str, set[str]]:
    """Map each `CREATE TABLE` to its set of column names."""
    tables: dict[str, set[str]] = {}
    for match in _TABLE_RE.finditer(sql):
        name = match.group(1).replace('"', "")
        columns: set[str] = set()
        for line in match.group(2).split("\n"):
            line = line.strip().rstrip(",")
            if not line or line.startswith(_NON_COLUMN_PREFIXES):
                continue
            columns.add(line.split()[0].replace('"', ""))
        tables[name] = columns
    return tables


@dataclass
class Drift:
    missing_from_schema_sql: set[str] = field(default_factory=set)
    missing_from_migrations: set[str] = field(default_factory=set)
    column_diffs: dict[str, tuple[set[str], set[str]]] = field(
        default_factory=dict
    )

    def __bool__(self) -> bool:
        return bool(
            self.missing_from_schema_sql
            or self.missing_from_migrations
            or self.column_diffs
        )

    def report(self) -> str:
        lines: list[str] = []
        for table in sorted(self.missing_from_schema_sql):
            lines.append(
                f"  {table}: created by migrations, absent from schema.sql"
            )
        for table in sorted(self.missing_from_migrations):
            lines.append(
                f"  {table}: in schema.sql, not created by migrations"
            )
        for table, (only_sql, only_mig) in sorted(self.column_diffs.items()):
            if only_sql:
                lines.append(
                    f"  {table}: columns only in schema.sql: "
                    f"{sorted(only_sql)}"
                )
            if only_mig:
                lines.append(
                    f"  {table}: columns only from migrations: "
                    f"{sorted(only_mig)}"
                )
        return "\n".join(lines)


def compare(migrated_sql: str, committed_sql: str) -> Drift:
    migrated = parse_tables(migrated_sql)
    committed = parse_tables(committed_sql)

    drift = Drift(
        missing_from_schema_sql=set(migrated) - set(committed),
        missing_from_migrations=(
            set(committed) - set(migrated) - UNMIGRATED_TABLES
        ),
    )
    for table in sorted(set(migrated) & set(committed)):
        only_sql = committed[table] - migrated[table]
        only_mig = migrated[table] - committed[table]
        if only_sql or only_mig:
            drift.column_diffs[table] = (only_sql, only_mig)
    return drift
