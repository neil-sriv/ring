from sqlalchemy import text
from pprintpp import pprint  # type: ignore
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script_di


@script_di()
def run_script(db: Session, query: str) -> None:
    print(f"Running query: {query}")
    results = db.execute(text(query))
    pprint(results.keys())
    pprint(results.fetchall())
