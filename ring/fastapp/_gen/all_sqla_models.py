def import_all_sqla_models() -> None:
    """Import all SQLAlchemy models."""
    from ring.key_value.models.model_key_value import ModelKeyValue
    from ring.letters.models.default_question_model import DefaultQuestion
    from ring.letters.models.letter_model import (
        Letter,
        letter_to_user_assocation,
    )
    from ring.letters.models.question_model import Question
    from ring.letters.models.response_model import (
        ImageResponseAssociation,
        Response,
    )
    from ring.notifications.models.subscription import Subscription
    from ring.parties.models.group_key_value import GroupKeyValue
    from ring.parties.models.group_model import Group
    from ring.parties.models.invite_model import Invite
    from ring.parties.models.one_time_token_model import OneTimeToken
    from ring.parties.models.user_group_assocation import (
        user_group_association,
    )
    from ring.parties.models.user_model import User
    from ring.s3.models.s3_model import Image, S3File
    from ring.tasks.models.schedule_model import Schedule
    from ring.tasks.models.task_model import (
        ReminderEmailTask,
        SendEmailTask,
        Task,
    )
