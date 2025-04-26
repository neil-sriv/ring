from sqlalchemy.orm import Session

from ring.lib.logger import logger
from ring.parties.crud import user as user_crud
from ring.scripts.script_base import script_di


@script_di()
def run_script(
    db: Session, dry_run: bool = True, user_emails: list[str] | None = None
) -> None:
    if user_emails is None:
        raise ValueError("user_emails is required")
    logger.info(f"Setting admin=True for {len(user_emails)} users")
    for user_email in user_emails:
        user = user_crud.get_user_by_email(db, user_email)
        if user is None:
            logger.error(f"User {user_email} not found")
            continue
        user_crud.make_user_admin(db, user)
    if dry_run:
        logger.info("Dry run, rolling back")
        db.rollback()
    else:
        db.commit()
