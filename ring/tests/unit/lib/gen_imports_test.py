"""Tests for the generated import-factory scanner and freshness check."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from ring.lib.gen_imports import (
    FACTORIES_PATH,
    JOBS_PATH,
    MODELS_PATH,
    SEARCH_PATH,
    ImportedName,
    ImportFactoryError,
    check_generated_imports,
    discover_api_classes,
    discover_factories,
    discover_job_modules,
    discover_job_names,
    discover_search_functions,
    discover_sqla_symbols,
    verify_api_classes_are_models,
)

# Names the hand-maintained factories imported before this generator.
HAND_MODEL_NAMES = frozenset(
    {
        "DefaultQuestion",
        "Document",
        "DocumentEdit",
        "Group",
        "GroupKeyValue",
        "HybridSearchDocument",
        "HybridSearchDocumentAssociation",
        "Image",
        "ImageResponseAssociation",
        "InboxItem",
        "Invite",
        "Letter",
        "ModelKeyValue",
        "OneTimeToken",
        "Question",
        "ReminderEmailTask",
        "Response",
        "S3File",
        "Schedule",
        "SendEmailTask",
        "Subscription",
        "Task",
        "User",
        "UserSpotifyPlaylist",
        "letter_to_user_assocation",
        "user_group_association",
    }
)
HAND_JOB_MODULES = frozenset(
    {
        "ring.fastapp.blindfold_job",
        "ring.letters.crud.letter",
        "ring.parties.crud.authn",
        "ring.parties.crud.invite",
        "ring.search.crud.integrity",
        "ring.tasks.crud.schedule",
        "ring.tasks.crud.task",
    }
)
HAND_SEARCH_NAMES = frozenset(
    {
        "create_group_search_document",
        "create_letter_search_document",
        "create_question_search_document",
        "create_response_search_document",
        "create_user_search_document",
    }
)
HAND_FACTORY_NAMES = frozenset(
    {
        "DefaultQuestionFactory",
        "DocumentEditFactory",
        "DocumentFactory",
        "GroupFactory",
        "InboxItemFactory",
        "InviteFactory",
        "LetterFactory",
        "OneTimeTokenFactory",
        "QuestionFactory",
        "ResponseFactory",
        "UserFactory",
    }
)


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source))


def _mini_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path
    ring = repo / "ring"
    _write(
        ring / "sqlalchemy_base.py",
        """
        from sqlalchemy.orm import DeclarativeBase
        class Base(DeclarativeBase):
            pass
        """,
    )
    _write(
        ring / "models" / "parent.py",
        """
        from ring.sqlalchemy_base import Base
        class Parent(Base):
            pass
        """,
    )
    _write(
        ring / "models" / "child.py",
        """
        from ring.models.parent import Parent
        class Child(Parent):
            pass
        """,
    )
    _write(
        ring / "models" / "kv.py",
        """
        from sqlalchemy.ext.declarative import AbstractConcreteBase
        from ring.sqlalchemy_base import Base
        class AbstractKV(AbstractConcreteBase, Base):
            pass
        class ConcreteKV(AbstractKV):
            pass
        """,
    )
    _write(
        ring / "models" / "assoc.py",
        """
        from sqlalchemy import Column, Integer, Table
        from ring.sqlalchemy_base import Base
        assoc = Table("assoc", Base.metadata, Column("id", Integer))
        """,
    )
    _write(
        ring / "jobs" / "mail.py",
        """
        from ring.async_scheduler.scheduler import job_factory
        @job_factory("send_mail")
        def send_mail():
            pass
        """,
    )
    _write(
        ring / "search" / "user.py",
        """
        from ring.search.crud.hybrid_search import register_search_function
        @register_search_function(None, None)
        def create_user_search_document():
            pass
        """,
    )
    _write(
        ring / "models" / "api.py",
        """
        from ring.api_identifier.util import register_api_class
        from ring.sqlalchemy_base import Base
        @register_api_class("usr")
        class ApiUser(Base):
            pass
        """,
    )
    factories = ring / "tests" / "factories"
    _write(
        factories / "user_factory.py",
        """
        from ring.tests.factories.base_factory import register_factory
        @register_factory
        class UserFactory:
            pass
        """,
    )
    return ring, factories


class TestDiscover:
    def test_models_include_indirect_and_tables(self, tmp_path: Path) -> None:
        ring, _factories = _mini_repo(tmp_path)
        names = {item.name for item in discover_sqla_symbols(ring, tmp_path)}
        assert names >= {
            "Parent",
            "Child",
            "AbstractKV",
            "ConcreteKV",
            "assoc",
            "ApiUser",
        }

    def test_job_modules_and_names(self, tmp_path: Path) -> None:
        ring, _factories = _mini_repo(tmp_path)
        assert discover_job_modules(ring, tmp_path) == ["ring.jobs.mail"]
        assert discover_job_names(ring, tmp_path) == ["send_mail"]

    def test_search_and_factories(self, tmp_path: Path) -> None:
        ring, factories = _mini_repo(tmp_path)
        assert discover_search_functions(ring, tmp_path) == [
            ImportedName("ring.search.user", "create_user_search_document")
        ]
        assert discover_factories(factories, tmp_path) == [
            ImportedName("ring.tests.factories.user_factory", "UserFactory")
        ]

    def test_api_class_must_be_a_model(self) -> None:
        models = [ImportedName("ring.models.api", "ApiUser")]
        missing = [ImportedName("ring.other", "Orphan")]
        with pytest.raises(ImportFactoryError, match="Orphan"):
            verify_api_classes_are_models(models, missing)


class TestRepoSuperset:
    def test_models_cover_hand_list(self) -> None:
        names = {item.name for item in discover_sqla_symbols()}
        assert HAND_MODEL_NAMES <= names

    def test_job_modules_cover_hand_list(self) -> None:
        assert HAND_JOB_MODULES <= set(discover_job_modules())

    def test_search_covers_hand_list(self) -> None:
        names = {item.name for item in discover_search_functions()}
        assert HAND_SEARCH_NAMES <= names

    def test_factories_cover_hand_list(self) -> None:
        names = {item.name for item in discover_factories()}
        assert HAND_FACTORY_NAMES <= names
        assert {"UpcomingLetterFactory", "AdminFactory"} <= names

    def test_api_classes_are_models(self) -> None:
        verify_api_classes_are_models(
            discover_sqla_symbols(), discover_api_classes()
        )


class TestGeneratedFilesFresh:
    def test_check_is_clean(self) -> None:
        assert check_generated_imports() == ""

    def test_generated_paths_exist(self) -> None:
        for path in (MODELS_PATH, JOBS_PATH, SEARCH_PATH, FACTORIES_PATH):
            text = path.read_text()
            assert text.startswith("# GENERATED - do not edit.")
            assert "schedule_all_interval_jobs" not in text
