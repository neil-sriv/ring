# """Tests for the search backfill script.

# This module provides tests for the search backfill script, ensuring it correctly
# creates and updates search documents for various model types.
# """

# from __future__ import annotations

# from unittest.mock import MagicMock, patch

# from sqlalchemy import delete, select

# from ring.scripts.dependencies import ScriptDependencies
# from ring.scripts.search.backfill import run_script
# from ring.search.crud.hybrid_search import (
#     get_model_ids_from_hybrid_search_documents,
#     hydrate_results,
# )
# from ring.search.models.hybrid_search import (
#     HybridSearchDocument,
#     SearchableType,
# )
# from ring.tests.factories.parties.user_factory import UserFactory
# from ring.tests.unit.scripts.script_tester import ScriptTestBase


# class TestSearchBackfill(ScriptTestBase):
#     """Test cases for the search backfill script."""

#     @patch("ring.search.crud.hybrid_search._generate_text_embedding")
#     def test_backfill_users(
#         self,
#         mock_generate_embedding: MagicMock,
#         script_deps: ScriptDependencies,
#     ):
#         """Test that the script correctly backfills search documents for users.

#         Args:
#             mock_generate_embedding (MagicMock): Mock for embedding generation
#             script_deps (ScriptDependencies): Script dependencies with test database session
#         """
#         # Set up mock embedding
#         mock_generate_embedding.return_value = [0.1] * 768

#         # Create test users
#         users = [UserFactory.create() for _ in range(3)]
#         script_deps.db.add_all(users)
#         script_deps.db.commit()
#         print(script_deps.db.query(HybridSearchDocument).all())
#         script_deps.db.execute(delete(HybridSearchDocument))
#         script_deps.db.commit()

#         # Run the script with dry_run=True
#         self.run(
#             run_script,
#             searchable_types=[SearchableType.USER],
#             dry_run=True,
#             deps=script_deps,
#         )

#         docs = script_deps.db.scalars(select(HybridSearchDocument)).all()
#         model_ids = get_model_ids_from_hybrid_search_documents(
#             script_deps.db, docs
#         )
#         assert (
#             len(model_ids.get(SearchableType.USER, [])) == 0
#         )  # No documents should exist after dry run

#         # Run the script with dry_run=False
#         self.run(
#             run_script,
#             searchable_types=[SearchableType.USER],
#             dry_run=False,
#             deps=script_deps,
#         )

#         # Verify documents were updated
#         docs = script_deps.db.scalars(select(HybridSearchDocument)).all()
#         print(docs)
#         model_ids = get_model_ids_from_hybrid_search_documents(
#             script_deps.db, docs
#         )
#         user_ids = model_ids.get(SearchableType.USER, [])
#         assert len(user_ids) == len(users)
#         assert all(user.api_identifier in user_ids for user in users)

#     @patch("ring.search.crud.hybrid_search._generate_text_embedding")
#     def test_replace_existing_documents(
#         self,
#         mock_generate_embedding: MagicMock,
#         script_deps: ScriptDependencies,
#     ):
#         """Test that the script correctly replaces existing search documents.

#         Args:
#             mock_generate_embedding (MagicMock): Mock for embedding generation
#             script_deps (ScriptDependencies): Script dependencies with test database session
#         """
#         # Set up mock embedding
#         mock_generate_embedding.return_value = [0.1] * 768

#         # Create test users
#         users = [UserFactory.create() for _ in range(3)]
#         script_deps.db.add_all(users)
#         script_deps.db.commit()
#         script_deps.db.expire_all()  # Clear session cache

#         # Run the script first time to create initial documents
#         self.run(
#             run_script,
#             searchable_types=[SearchableType.USER],
#             dry_run=False,
#             deps=script_deps,
#         )

#         # Get initial document IDs
#         initial_docs = script_deps.db.scalars(
#             select(HybridSearchDocument)
#         ).all()
#         initial_doc_ids = [doc.id for doc in initial_docs]

#         # Run the script with replace_existing=True
#         self.run(
#             run_script,
#             searchable_types=[SearchableType.USER],
#             replace_existing=True,
#             dry_run=False,
#             deps=script_deps,
#         )

#         # Verify new documents were created
#         new_docs = script_deps.db.scalars(select(HybridSearchDocument)).all()
#         new_doc_ids = [doc.id for doc in new_docs]

#         # Check that we have the same number of documents
#         assert len(new_docs) == len(initial_docs)
#         # Check that the IDs are different (documents were replaced)
#         assert set(new_doc_ids) != set(initial_doc_ids)

#     @patch("ring.search.crud.hybrid_search._generate_text_embedding")
#     def test_partial_backfill(
#         self,
#         mock_generate_embedding: MagicMock,
#         script_deps: ScriptDependencies,
#     ):
#         """Test that the script correctly handles partial backfill of documents.

#         Args:
#             mock_generate_embedding (MagicMock): Mock for embedding generation
#             script_deps (ScriptDependencies): Script dependencies with test database session
#         """
#         # Set up mock embedding
#         mock_generate_embedding.return_value = [0.1] * 768

#         # Create test users
#         users = [UserFactory.create() for _ in range(3)]
#         script_deps.db.add_all(users)
#         script_deps.db.commit()
#         script_deps.db.expire_all()  # Clear session cache

#         # Run the script without replace_existing
#         self.run(
#             run_script,
#             searchable_types=[SearchableType.USER],
#             dry_run=False,
#             deps=script_deps,
#         )

#         # Verify all documents exist
#         docs = script_deps.db.scalars(select(HybridSearchDocument)).all()
#         model_ids = get_model_ids_from_hybrid_search_documents(
#             script_deps.db, docs
#         )
#         user_ids = model_ids.get(SearchableType.USER, [])
#         assert len(user_ids) == len(users)  # All users should have documents
#         assert all(user.api_identifier in user_ids for user in users)

#     @patch("ring.search.crud.hybrid_search._generate_text_embedding")
#     def test_all_searchable_types(
#         self,
#         mock_generate_embedding: MagicMock,
#         script_deps: ScriptDependencies,
#     ):
#         """Test that the script correctly handles all searchable types.

#         Args:
#             mock_generate_embedding (MagicMock): Mock for embedding generation
#             script_deps (ScriptDependencies): Script dependencies with test database session
#         """
#         # Set up mock embedding
#         mock_generate_embedding.return_value = [0.1] * 768

#         # Create test users
#         users = [UserFactory.create() for _ in range(3)]
#         script_deps.db.add_all(users)
#         script_deps.db.commit()
#         script_deps.db.expire_all()  # Clear session cache

#         # Run the script with all searchable types
#         self.run(
#             run_script,
#             searchable_types=None,  # Should use all types
#             dry_run=False,
#             deps=script_deps,
#         )

#         docs = script_deps.db.scalars(select(HybridSearchDocument)).all()
#         model_ids = get_model_ids_from_hybrid_search_documents(
#             script_deps.db, docs
#         )
#         user_ids = model_ids.get(SearchableType.USER, [])
#         assert len(user_ids) == len(users)
#         assert all(user.api_identifier in user_ids for user in users)
