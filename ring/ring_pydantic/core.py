"""Core Pydantic models for common response types."""

from __future__ import annotations

from pydantic import BaseModel


class ResponseMessage(BaseModel):
    """Standard response message model.

    Used for API endpoints that return a simple message response.

    Attributes:
        message (str): The response message text
    """
    message: str
