"""Logger configuration module for the Ring application.

This module configures loguru for application-wide logging with two handlers:
1. Console output with INFO level and colorized formatting
2. File output with DEBUG level, JSON serialization, and rotation/retention policies

The logger can be imported and used throughout the application as:
    from ring.lib.logger import logger
"""
from __future__ import annotations

import sys

from loguru import logger

# Remove default handler to avoid duplicate logs
logger.remove()

# Add console handler with colorized output for INFO and above
logger.add(
    sys.stdout, format="{time} {level} {message}", level="INFO", colorize=True
)

# Add file handler with JSON serialization and rotation for all DEBUG and above
logger.add(
    "logs/app.log",
    rotation="10 MB",  # Rotate logs when they reach 10MB
    retention="30 days",  # Keep logs for 30 days
    level="DEBUG",
    serialize=True,  # Store logs as JSON for structured logging
)
