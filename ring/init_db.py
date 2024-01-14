import os
from ring.postgres_models import User
from ring.sqlalchemy_base import SessionLocal


def init_db():
    db = SessionLocal()
    db.query(User).exists()
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
