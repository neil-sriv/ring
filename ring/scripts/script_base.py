import functools
from typing import Any, Callable
from ring.sqlalchemy_base import Session, db_session, T


def script_di() -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        @db_session
        @functools.wraps(f)
        def inner(db: Session, *args: Any, **kwargs: Any) -> T:
            return f(db, *args, **kwargs)

        return inner

    return decorator


@script_di()
def run_script(db: Session) -> None:
    raise NotImplementedError()
