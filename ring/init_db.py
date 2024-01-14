import os
from ring.pynamo_models.email_model import ScheduleModel
from ring.pynamo_models.letter_model import GroupModel


def init_db():
    if not GroupModel.exists():
        GroupModel.create_table(
            read_capacity_units=1, write_capacity_units=1, wait=True
        )
        migrate()
    if not ScheduleModel.exists():
        ScheduleModel.create_table(
            read_capacity_units=1, write_capacity_units=1, wait=True
        )
    pass


def migrate():
    # migrate issues
    print("Migrating issues")
    with open("issues/adults/1.txt", "r") as f:
        lines = f.readlines()
    print(lines)


if __name__ == "__main__":
    init_db()
    # migrate()
