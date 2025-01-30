import sys

from loguru import logger

# Remove default handler
logger.remove()

# Add a new handler with formatting
logger.add(
    sys.stdout, format="{time} {level} {message}", level="INFO", colorize=True
)

logger.add(
    "logs/app.log",
    rotation="10 MB",  # Rotate logs when they reach 10MB
    retention="30 days",  # Keep logs for 10 days
    level="DEBUG",
    serialize=True,  # Store logs as JSON
)
