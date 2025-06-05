"""Base class for script testing.

This module provides a base class for testing Ring scripts with proper dependency injection.
"""

from __future__ import annotations

from typing import Any, Callable

from ring.scripts.dependencies import ScriptDependencies


class ScriptTestBase:
    """Base class for script testing.

    This class provides utilities for running scripts in a test environment
    with proper dependency injection.
    """

    def run(
        self,
        run_script: Callable[..., Any],
        deps: ScriptDependencies | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run a script with optional dependencies.

        Args:
            run_script (Callable[..., Any]): The script function to run
            deps (ScriptDependencies | None): Optional dependencies to inject
            *args (Any): Additional positional arguments for the script
            **kwargs (Any): Additional keyword arguments for the script

        Returns:
            Any: The result of running the script
        """
        if deps is not None:
            return run_script(deps=deps, *args, **kwargs)
        return run_script(*args, **kwargs)
