# GENERATED - do not edit. Regenerate with `ring gen imports`.

from __future__ import annotations


def import_all_jobs() -> None:
    """Import all jobs."""
    import ring.async_scheduler.scheduler
    import ring.fastapp.blindfold_job
    import ring.letters.crud.letter
    import ring.parties.crud.authn
    import ring.parties.crud.invite
    import ring.search.crud.integrity
    import ring.tasks.crud.schedule
    import ring.tasks.crud.task


def initialize() -> None:
    import_all_jobs()
