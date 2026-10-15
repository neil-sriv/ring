"""Tests for the identity-service backfill script."""

from __future__ import annotations

from ring.auth.dual_sync.metrics import metrics
from ring.auth.idp_client.factory import set_identity_client_override
from ring.auth.idp_client.fake import FakeIdentityClient
from ring.scripts.dependencies import ScriptDependencies
from ring.scripts.parties.backfill_authn_identities import run_script
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.scripts.script_tester import ScriptTestBase


class TestBackfillAuthnIdentities(ScriptTestBase):
    def setup_method(self) -> None:
        self.fake = FakeIdentityClient()
        set_identity_client_override(self.fake)
        metrics.reset()

    def teardown_method(self) -> None:
        set_identity_client_override(None)
        metrics.reset()

    def test_dry_run_does_not_call_idp(
        self, script_deps: ScriptDependencies
    ) -> None:
        UserFactory.create()
        script_deps.db.commit()
        result = self.run(run_script, dry_run=True, deps=script_deps)
        assert result["users"] == 1
        assert result["succeeded"] == 1
        assert self.fake.upsert_calls == []

    def test_upserts_all_users_by_api_identifier(
        self, script_deps: ScriptDependencies
    ) -> None:
        users = [UserFactory.create() for _ in range(3)]
        script_deps.db.commit()
        result = self.run(run_script, dry_run=False, deps=script_deps)
        assert result["users"] == 3
        assert result["failed"] == 0
        assert result["succeeded"] == 3
        ids = {call.external_id for call in self.fake.upsert_calls}
        assert ids == {user.api_identifier for user in users}
        hashes = {user.api_identifier: user.hashed_password for user in users}
        for call in self.fake.upsert_calls:
            assert call.external_id.startswith("usr_")
            assert call.hashed_password == hashes[call.external_id]
            assert call.hashed_password.startswith("$")

    def test_idempotent_second_run(
        self, script_deps: ScriptDependencies
    ) -> None:
        UserFactory.create()
        script_deps.db.commit()
        self.run(run_script, dry_run=False, deps=script_deps)
        self.run(run_script, dry_run=False, deps=script_deps)
        assert len(self.fake.upsert_calls) == 2
        assert len(self.fake.identities) == 1

    def test_failures_are_counted_not_raised(
        self, script_deps: ScriptDependencies
    ) -> None:
        UserFactory.create()
        script_deps.db.commit()
        self.fake.fail_upserts = True
        result = self.run(run_script, dry_run=False, deps=script_deps)
        assert result["failed"] == 1
        assert result["succeeded"] == 0
