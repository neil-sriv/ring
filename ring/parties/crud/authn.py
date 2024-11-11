from ring.email_util import CHARSET, EmailDraft, send_email
from ring.parties.models.user_model import User
from ring.security import get_password_hash
from ring.worker.celery_app import CeleryTask, register_task_factory


def reset_user_password(db_user: User, new_password: str) -> None:
    db_user.hashed_password = get_password_hash(new_password)


@register_task_factory(name="email_password_reset")
def email_password_reset(self: CeleryTask, email: str, token: str) -> None:
    email_draft = construct_password_reset_email(email, token)
    send_email(email_draft)


def construct_password_reset_email(
    recipient: str,
    token: str,
) -> EmailDraft:
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
