from __future__ import annotations

from sqlalchemy.orm import Session

from ring.async_scheduler.scheduler import job_factory
from ring.email_util import CHARSET, EmailDraft, send_email
from ring.parties.models.user_model import User
from ring.security import get_password_hash


def reset_user_password(db_user: User, new_password: str) -> None:
    """Reset a user's password with a new hashed password.

    Args:
        db_user (User): User whose password needs to be reset
        new_password (str): New password to set (will be hashed)
    """
    db_user.hashed_password = get_password_hash(new_password)


@job_factory("email_password_reset")
def email_password_reset(db: Session, email: str, token: str) -> None:
    """Send a password reset email to a user.

    This is a job that constructs and sends a password reset email
    containing a reset token.

    Args:
        db (Session): Database session
        email (str): Recipient's email address
        token (str): Password reset token
    """
    email_draft = construct_password_reset_email(email, token)
    send_email(email_draft)


def construct_password_reset_email(
    recipient: str,
    token: str,
) -> EmailDraft:
    """Construct an email draft for password reset.

    Creates an HTML email containing a link with a password reset token.

    Args:
        recipient (str): Email address of the recipient
        token (str): Password reset token to include in the reset link

    Returns:
        EmailDraft: Email draft ready to be sent
    """
    BODY_HTML = """
    <html>
    <head></head>
    <body>
    <h1 style="text-align:center">Reset password for your Ring account</h1>
    <spacer type="" size="">
    <span>Click the link below to reset your password.</span>
    <spacer type="" size="">
    <h3>Please use this custom URL to reset your password: <a href="http://ring.neilsriv.tech/reset-password/{token}">http://ring.neilsriv.tech/reset-password/{token}</a></h2>
    <p>
    A password reset was requested for your Ring account. If you did not request this, please ignore this email.
    </p>
    </body>
    </html>
                """.format(token=token)
    return EmailDraft(
        destination={"ToAddresses": [recipient]},
        message={
            "Subject": {
                "Data": "Ring: Password reset requested!",
                "Charset": CHARSET,
            },
            "Body": {
                "Html": {
                    "Data": BODY_HTML,
                    "Charset": CHARSET,
                },
            },
        },
    )
