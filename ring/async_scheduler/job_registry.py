"""Global job registry for managing scheduled jobs.

This module provides a centralized registry for all scheduled jobs,
following the registration patterns used throughout the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from loguru import logger

from ring.lib.util import RegistrationDict

JOB_RETURN_TYPE = Any


@dataclass
class JobRegistration:
    """Registration information for a scheduled job.

    Attributes:
        name: The unique name of the job
        job_function: The actual job function to execute
    """

    name: str
    job_function: Callable[..., JOB_RETURN_TYPE]


# Global job registry
JOB_REGISTRY: RegistrationDict[str, JobRegistration] = RegistrationDict(
    "JOB_REGISTRY"
)


def register_job(
    name: str,
    job_function: Callable[..., JOB_RETURN_TYPE],
) -> None:
    """Register a job with the global job registry.

    Args:
        name: The unique name of the job
        job_function: The job function to register
    """
    JOB_REGISTRY[name] = JobRegistration(
        name=name,
        job_function=job_function,
    )

    # logger.info(f"Registered job '{name}'")
