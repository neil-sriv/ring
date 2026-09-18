from __future__ import annotations


def hydrate_factories_registry():
    from ring.tests.factories.letters.default_question_factory import (
        DefaultQuestionFactory,
    )
    from ring.tests.factories.letters.letter_factory import LetterFactory
    from ring.tests.factories.letters.question_factory import QuestionFactory
    from ring.tests.factories.letters.response_factory import ResponseFactory
    from ring.tests.factories.notebook.document_factory import (
        DocumentEditFactory,
        DocumentFactory,
    )
    from ring.tests.factories.notifications.notification_factory import (
        NotificationFactory,
    )
    from ring.tests.factories.parties.group_factory import GroupFactory
    from ring.tests.factories.parties.invite_factory import InviteFactory
    from ring.tests.factories.parties.one_time_token_factory import (
        OneTimeTokenFactory,
    )
    from ring.tests.factories.parties.user_factory import UserFactory


def hydrate_all_registries():
    hydrate_factories_registry()
