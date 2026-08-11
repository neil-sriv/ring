"""Tests for slim search result serialization."""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.orm import Session

from ring.search.crud.search_serialization import build_search_results
from ring.search.schemas.search_snippets import SearchUserSnippet
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestSearchSerialization:
    def test_build_user_snippets_uses_count_query_not_relationship_load(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        group = GroupFactory.create()
        group.members.append(user)
        db_session.commit()

        query_count = 0

        def count_queries(
            conn, cursor, statement, parameters, context, executemany
        ) -> None:
            nonlocal query_count
            query_count += 1

        event.listen(
            db_session.get_bind(),
            "before_cursor_execute",
            count_queries,
        )
        try:
            results = build_search_results(db_session, [user])
        finally:
            event.remove(
                db_session.get_bind(),
                "before_cursor_execute",
                count_queries,
            )

        assert len(results) == 1
        assert results[0].type == SearchUserSnippet.__name__
        snippet = results[0].model
        assert isinstance(snippet, SearchUserSnippet)
        assert snippet.api_identifier == user.api_identifier
        assert snippet.name == user.name
        assert snippet.group_count == 1
        assert query_count <= 2
