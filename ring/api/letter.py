from ring.fast import app
from ring.pynamo_models.letter_model import GroupModel


@app.get("/group/{group_id}")
def get_groups(group_id: str):
    return GroupModel.get(group_id)


@app.get("/user/{user_id}/groups")
def get_user_groups(user_id: str):
    groups = GroupModel.query(GroupModel.members.)