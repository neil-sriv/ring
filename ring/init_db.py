from ring.models import GroupModel


def init_db():
    GroupModel.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)


if __name__ == "__main__":
    init_db()
