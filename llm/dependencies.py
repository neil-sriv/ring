from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends

from llm.security.security import get_api_key


@dataclass
class RequestDependenciesBase:
    """Base class for request dependencies"""

    pass


@dataclass
class AuthenticatedRequestDependencies(RequestDependenciesBase):
    """Dependencies for authenticated requests"""

    api_key: str


async def get_request_dependencies() -> RequestDependenciesBase:
    """Get basic request dependencies"""
    return RequestDependenciesBase()


async def get_authenticated_request_dependencies(
    api_key: str = Depends(get_api_key),
) -> AuthenticatedRequestDependencies:
    """Get dependencies for authenticated requests"""
    return AuthenticatedRequestDependencies(api_key=api_key)


async def get_unauthenticated_request_dependencies() -> (
    RequestDependenciesBase
):
    """Get dependencies for unauthenticated requests"""
    return RequestDependenciesBase()
