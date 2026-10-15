"""Runtime checks that generated imports fill the decorator registries."""

from __future__ import annotations

import re
from pathlib import Path

from ring.api_identifier.api_identified_model import APIPrefix
from ring.api_identifier.util import API_CLASS_REGISTRY
from ring.async_scheduler.job_registry import JOB_REGISTRY
from ring.fastapp._gen.all_jobs import import_all_jobs
from ring.fastapp._gen.all_sqla_models import import_all_sqla_models
from ring.lib.gen_imports import discover_job_names
from ring.search._gen.all_search_registration import (
    import_all_search_registrations,
)
from ring.search.crud.hybrid_search import SEARCH_REGISTRY
from ring.search.models.hybrid_search import SearchableType
from ring.sqlalchemy_base import Base

SCHEMA_SQL = Path(__file__).resolve().parents[3] / "db" / "schema.sql"
CREATE_TABLE_RE = re.compile(r'CREATE TABLE public\."?([A-Za-z0-9_]+)"?')
ALEMBIC_VERSION_TABLE = "alembic_version"


class TestRegistries:
    def test_every_searchable_type_is_registered(self) -> None:
        import_all_search_registrations()
        for searchable_type in SearchableType:
            assert searchable_type in SEARCH_REGISTRY

    def test_every_api_prefix_is_registered(self) -> None:
        import_all_sqla_models()
        for prefix in APIPrefix:
            assert prefix in API_CLASS_REGISTRY

    def test_schema_tables_are_in_metadata(self) -> None:
        import_all_sqla_models()
        import_all_jobs()
        tables = set(CREATE_TABLE_RE.findall(SCHEMA_SQL.read_text()))
        tables.discard(ALEMBIC_VERSION_TABLE)
        missing = tables - set(Base.metadata.tables)
        assert missing == set()

    def test_discovered_jobs_are_in_registry(self) -> None:
        import_all_jobs()
        missing = set(discover_job_names()) - set(JOB_REGISTRY)
        assert missing == set()
        assert {
            "send_response_open_email",
            "send_waiting_response_email",
            "test_job",
        } <= set(JOB_REGISTRY)
