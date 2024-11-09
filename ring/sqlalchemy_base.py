from typing import Any, Callable, Iterator, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ring.config import get_config

engine = create_engine(
    get_config().sqlalchemy_database_uri,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


Base()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


T = TypeVar("T")


# decorator injects a database session
def db_session(func: Callable[..., T]) -> Callable[..., T]:
    def wrapper(*args: Any, **kwargs: Any) -> T:
        db = next(get_db())
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close()

    return wrapper
