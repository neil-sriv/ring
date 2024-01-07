from ring.models.letter_model import GroupModel


def email_groups(group_id: str) -> None:
    group = GroupModel.get(group_id)
    pass


def construct_email(group: GroupModel) -> str:
    pass
