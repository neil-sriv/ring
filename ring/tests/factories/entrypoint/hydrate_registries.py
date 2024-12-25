def hydrate_factories_registry():
    from ring.tests.factories.parties.group_factory import GroupFactory
    from ring.tests.factories.parties.invite_factory import InviteFactory
    from ring.tests.factories.parties.one_time_token_factory import (
        OneTimeTokenFactory,
    )
    from ring.tests.factories.parties.user_factory import UserFactory


def hydrate_all_registries():
    hydrate_factories_registry()
