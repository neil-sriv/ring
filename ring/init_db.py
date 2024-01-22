from ring.sqlalchemy_base import Base, engine


def init_db():
    import ring.postgres_models

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
