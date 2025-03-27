"""List of Celery task modules to import.

This module defines the list of Python modules containing Celery tasks that should be
automatically imported and registered with the Celery worker. This ensures all Ring's
asynchronous tasks are properly discovered and available for execution.
"""

CELERY_IMPORTS = [
    "ring.tasks.crud.task",
    "ring.tasks.crud.schedule",
    "ring.letters.crud.letter",
    "ring.parties.crud.invite",
    "ring.parties.crud.authn",
]
