from ring.postgres_models import User, Group, Letter, Question, Response
from ring.sqlalchemy_base import Base, engine


def init_db():
    # for table in [User, Group, Letter, Question, Response]:
    # if table.__table__.exists():
    # table.__table__.drop(bind=engine)
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
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
