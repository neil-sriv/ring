"""Script to backfill admin status for specified users."""

from __future__ import annotations

from ring.lib.logger import logger
from ring.parties.crud import user as user_crud
from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)


def run_script(
    user_emails: list[str] | None = None,
    dry_run: bool = True,
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> None:
    """Set admin status for specified users.

    Args:
        user_emails (list[str] | None): List of user emails to make admin
        dry_run (bool): Whether to commit changes
        deps (ScriptDependencies): Script dependencies provided by script_depends

    Raises:
        ValueError: If user_emails is not provided
    """
    if user_emails is None:
        raise ValueError("user_emails is required")
    logger.info(f"Setting admin=True for {len(user_emails)} users")
    for user_email in user_emails:
        user = user_crud.get_user_by_email(deps.db, user_email)
        if user is None:
            logger.error(f"User {user_email} not found")
            continue
        user_crud.make_user_admin(deps.db, user)
    if dry_run:
        logger.info("Dry run, rolling back")
        deps.db.rollback()
    else:
        deps.db.commit()
