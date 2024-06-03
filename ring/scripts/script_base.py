from typing import Any, Callable
from ring.sqlalchemy_base import Session, get_db


# decorator for scripts that injects a database session
def script(func: Callable[..., None]) -> Callable[..., None]:
    def wrapper(*args: Any, **kwargs: Any) -> None:
        db = next(get_db())
        try:
            func(db, *args, **kwargs)
        finally:
            db.close()

    return wrapper


@script
def run_script(db: Session) -> None:
    raise NotImplementedError()
