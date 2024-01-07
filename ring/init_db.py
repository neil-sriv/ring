from ring.models.email_model import ScheduleModel
from ring.models.letter_model import GroupModel


def init_db():
    if not GroupModel.exists():
        GroupModel.create_table(
            read_capacity_units=1, write_capacity_units=1, wait=True
        )
        migrate_groups()
    if not ScheduleModel.exists():
        ScheduleModel.create_table(
            read_capacity_units=1, write_capacity_units=1, wait=True
        )


def migrate_groups():
    pass


if __name__ == "__main__":
    init_db()
