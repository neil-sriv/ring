"""One-shot backfill for the permission_grant migration.

Imported by that revision. Do not edit these statements after the migration
ships; add another revision instead.

Group roles are copied into grants: the group's admin user receives ``admin``
on the group, every other member receives ``member``. Letters do not store a
creator. For each existing adhoc letter, the earliest authored question whose
author is still a member of the letter's group is the only stored actor, and
that user receives ``admin`` on the letter.
"""

from __future__ import annotations

BACKFILL_GROUP_ADMINS = """
INSERT INTO permission_grant (subject_api_id, resource_api_id, permission)
SELECT u.api_identifier, g.api_identifier, 'admin'
FROM "group" g
JOIN "user" u ON u.id = g.admin_id
ON CONFLICT (subject_api_id, resource_api_id, permission) DO NOTHING
"""

BACKFILL_GROUP_MEMBERS = """
INSERT INTO permission_grant (subject_api_id, resource_api_id, permission)
SELECT u.api_identifier, g.api_identifier, 'member'
FROM user_group_assocation AS membership
JOIN "user" u ON u.id = membership.user_id
JOIN "group" g ON g.id = membership.group_id
WHERE u.id IS DISTINCT FROM g.admin_id
ON CONFLICT (subject_api_id, resource_api_id, permission) DO NOTHING
"""

BACKFILL_ADHOC_LOOP_ADMINS = """
INSERT INTO permission_grant (subject_api_id, resource_api_id, permission)
SELECT creator.subject_api_id, creator.resource_api_id, 'admin'
FROM (
    SELECT DISTINCT ON (letter.id)
        author.api_identifier AS subject_api_id,
        letter.api_identifier AS resource_api_id
    FROM letter
    JOIN question ON question.letter_id = letter.id
    JOIN "user" AS author ON author.id = question.author_id
    JOIN user_group_assocation AS membership
        ON membership.group_id = letter.group_id
        AND membership.user_id = author.id
    WHERE letter.letter_type = 'ADHOC'
        AND question.author_id IS NOT NULL
    ORDER BY letter.id, question.created_at ASC, question.id ASC
) AS creator
ON CONFLICT (subject_api_id, resource_api_id, permission) DO NOTHING
"""

BACKFILL_STATEMENTS = (
    BACKFILL_GROUP_ADMINS,
    BACKFILL_GROUP_MEMBERS,
    BACKFILL_ADHOC_LOOP_ADMINS,
)
