from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RequestDependenciesBase:
    """Base class for request dependencies"""
    pass


@dataclass
class AuthenticatedRequestDependencies(RequestDependenciesBase):
    """Dependencies for authenticated requests"""
    pass


async def get_request_dependencies() -> RequestDependenciesBase:
    """Get basic request dependencies"""
    return RequestDependenciesBase()


async def get_unauthenticated_request_dependencies() -> RequestDependenciesBase:
    """Get dependencies for unauthenticated requests"""
    return RequestDependenciesBase() 