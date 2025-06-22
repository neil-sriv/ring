from __future__ import annotations

from casbin import Enforcer, util


def get_enforcer() -> Enforcer:
    """Get the enforcer for the authz system."""
    return Enforcer("/src/ring/authz/model.conf", "/src/ring/authz/policy.csv")
