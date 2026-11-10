"""Baseline grants from group roles, and permission checks over those rows."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from ring.authz.backfill import BACKFILL_STATEMENTS
from ring.authz.grants import grant_permission, holds_permission
from ring.authz.permission_grant import Permission, PermissionGrant
from ring.letters.constants import LetterType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


def _permissions(
    db: Session, subject_api_id: str, resource_api_id: str
) -> set[str]:
    return set(
        db.scalars(
            select(PermissionGrant.permission).where(
                PermissionGrant.subject_api_id == subject_api_id,
                PermissionGrant.resource_api_id == resource_api_id,
            )
        ).all()
    )


class TestBaselineGrants:
    def test_group_roles_write_admin_and_member_grants(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        member = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, member])
        db_session.flush()

        assert _permissions(
            db_session, admin.api_identifier, group.api_identifier
        ) == {Permission.ADMIN.value}
        assert _permissions(
            db_session, member.api_identifier, group.api_identifier
        ) == {Permission.MEMBER.value}
        assert holds_permission(db_session, admin, Permission.ADMIN, group)
        assert holds_permission(db_session, admin, Permission.MEMBER, group)
        assert not holds_permission(
            db_session, member, Permission.ADMIN, group
        )
        assert holds_permission(db_session, member, Permission.MEMBER, group)

    def test_group_admin_grant_covers_every_loop(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        member = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, member])
        cyclic = LetterFactory.create(group=group)
        adhoc = LetterFactory.create(
            group=group, letter_type=LetterType.ADHOC, number=None
        )
        db_session.flush()

        assert holds_permission(db_session, admin, Permission.ADMIN, cyclic)
        assert holds_permission(db_session, admin, Permission.ADMIN, adhoc)
        assert not holds_permission(
            db_session, member, Permission.ADMIN, cyclic
        )
        assert not holds_permission(
            db_session, member, Permission.ADMIN, adhoc
        )
        assert holds_permission(db_session, member, Permission.MEMBER, adhoc)

    def test_loop_admin_grant_covers_only_that_loop(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        member = UserFactory.create()
        other = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, member, other]
        )
        own = LetterFactory.create(
            group=group, letter_type=LetterType.ADHOC, number=None
        )
        theirs = LetterFactory.create(
            group=group, letter_type=LetterType.ADHOC, number=None
        )
        db_session.flush()
        grant_permission(
            db_session,
            member.api_identifier,
            own.api_identifier,
            Permission.ADMIN,
        )
        db_session.flush()

        assert holds_permission(db_session, member, Permission.ADMIN, own)
        assert not holds_permission(
            db_session, member, Permission.ADMIN, theirs
        )
        assert not holds_permission(
            db_session, member, Permission.ADMIN, group
        )
        assert not holds_permission(db_session, other, Permission.ADMIN, own)

    def test_removed_member_loses_group_and_loop_grants(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        member = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, member])
        letter = LetterFactory.create(
            group=group, letter_type=LetterType.ADHOC, number=None
        )
        db_session.flush()
        grant_permission(
            db_session,
            member.api_identifier,
            letter.api_identifier,
            Permission.ADMIN,
        )
        db_session.flush()
        group.members.remove(member)
        db_session.flush()

        assert (
            _permissions(
                db_session, member.api_identifier, group.api_identifier
            )
            == set()
        )
        assert (
            _permissions(
                db_session, member.api_identifier, letter.api_identifier
            )
            == set()
        )
        assert not holds_permission(
            db_session, member, Permission.ADMIN, letter
        )
        assert not holds_permission(
            db_session, member, Permission.MEMBER, group
        )


class TestBackfill:
    def test_backfill_restores_roles_and_adhoc_creator(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        creator = UserFactory.create()
        other = UserFactory.create()
        outsider = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, creator, other]
        )
        letter = LetterFactory.create(
            group=group,
            letter_type=LetterType.ADHOC,
            number=None,
            title="Off cycle",
        )
        authored = QuestionFactory.create(
            letter=letter, author=creator, question_text="from creator"
        )
        later = QuestionFactory.create(
            letter=letter, author=other, question_text="from other"
        )
        QuestionFactory.create(
            letter=letter,
            author=outsider,
            question_text="not a member",
        )
        untouched = LetterFactory.create(
            group=group, letter_type=LetterType.ADHOC, number=None
        )
        db_session.flush()
        authored.created_at = datetime.now(tz=UTC) - timedelta(days=2)
        later.created_at = datetime.now(tz=UTC) - timedelta(days=1)
        db_session.flush()

        db_session.execute(delete(PermissionGrant))
        db_session.flush()
        for statement in BACKFILL_STATEMENTS:
            db_session.execute(text(statement))
        db_session.flush()
        db_session.expire_all()

        assert _permissions(
            db_session, admin.api_identifier, group.api_identifier
        ) == {Permission.ADMIN.value}
        assert _permissions(
            db_session, creator.api_identifier, group.api_identifier
        ) == {Permission.MEMBER.value}
        assert _permissions(
            db_session, other.api_identifier, group.api_identifier
        ) == {Permission.MEMBER.value}
        assert _permissions(
            db_session, creator.api_identifier, letter.api_identifier
        ) == {Permission.ADMIN.value}
        assert (
            _permissions(
                db_session, other.api_identifier, letter.api_identifier
            )
            == set()
        )
        assert (
            _permissions(
                db_session, outsider.api_identifier, letter.api_identifier
            )
            == set()
        )
        assert (
            _permissions(
                db_session, creator.api_identifier, untouched.api_identifier
            )
            == set()
        )
        assert holds_permission(db_session, creator, Permission.ADMIN, letter)
        assert not holds_permission(
            db_session, creator, Permission.ADMIN, untouched
        )
