from __future__ import annotations


def import_all_search_registrations() -> None:
    """Import all search registrations."""
    from ring.letters.crud.letter import create_letter_search_document
    from ring.letters.crud.question import create_question_search_document
    from ring.letters.crud.response import create_response_search_document
    from ring.parties.crud.group import create_group_search_document
    from ring.parties.crud.user import create_user_search_document
    from ring.search.crud.hybrid_search import register_search_function
    from ring.search.models.hybrid_search import HybridSearchDocument
