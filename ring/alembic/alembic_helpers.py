from __future__ import annotations

from sqlalchemy import JSON, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TIMESTAMP as PG_TIMESTAMP


def include_object(object_, name, type_, reflected, compare_to):
    """Filter objects to include in Alembic migrations.

    This function is called by Alembic during migration generation to determine
    which database objects should be included in the migration.

    Args:
        object_ (object): The SQLAlchemy object being considered for migration
        name (str): Name of the database object
        type_ (str): Type of object (e.g., 'table', 'column', 'index')
        reflected (bool): Whether the object was reflected from the database
        compare_to (object): The corresponding object from the metadata, if any

    Returns:
        bool: True if the object should be included in the migration, False otherwise

    Note:
        Currently excludes timestamp columns named 'created_at' and 'updated_at'
        as these are typically managed by application-level triggers or ORM.
    """

    if type_ == "table":
        if name == "apscheduler_jobs":
            return False

    if type_ == "index":
        if name == "ix_apscheduler_jobs_next_run_time":
            return False
        if compare_to is not None:
            # Compare both column names and uniqueness
            same_columns = getattr(object_, "column_names", None) == getattr(
                compare_to, "column_names", None
            )
            same_unique = getattr(object_, "unique", None) == getattr(
                compare_to, "unique", None
            )

            if same_columns and same_unique:
                print(
                    f"[Alembic] Suppressing NULLS ordering diff for index {name}"
                )
                return False  # skip migration

    return True


def cockroach_compare_type(
    context, inspected_column, metadata_column, inspected_type, metadata_type
):
    """Compare column types between database and metadata for CockroachDB compatibility.

    This function handles special cases for timestamp columns in CockroachDB,
    particularly around timezone handling.

    Args:
        context: The Alembic migration context
        inspected_column: The column as reflected from the database
        metadata_column: The column as defined in the SQLAlchemy metadata
        inspected_type: The type of the column as reflected from the database
        metadata_type: The type of the column as defined in the metadata

    Returns:
        bool: False if the types should be considered equivalent, None to use default comparison
    """
    # Only intervene if we are looking at timestampish columns
    if isinstance(inspected_type, (DateTime, PG_TIMESTAMP)) and isinstance(
        metadata_type, DateTime
    ):
        # If model expects timezone, and DB reflection lost timezone info, ignore
        if getattr(metadata_type, "timezone", False):
            print(
                f"[Alembic] Ignoring TIMESTAMP timezone mismatch on column: {inspected_column.name}"
            )
            return False  # Tell Alembic: "no real diff"

    # Handle JSON vs JSONB
    if isinstance(inspected_type, (JSON, JSONB)) and isinstance(
        metadata_type, JSONB
    ):
        print(
            f"[Alembic] Suppressing false JSON vs JSONB mismatch on {inspected_column.name}"
        )
        return False  # treat JSON and JSONB as compatible
    # Otherwise, fall back to Alembic default
    return None
