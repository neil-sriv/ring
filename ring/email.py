from ring.models.letter_model import GroupModel
import boto3


def email_group(group_id: str) -> None:
    group = GroupModel.get(group_id)
    email = construct_email(group)
    ses_client = boto3.client("ses")
    pass


def construct_email(group: GroupModel) -> str:
    pass
