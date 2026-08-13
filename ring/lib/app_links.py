"""Absolute links into the web app, for use in outbound email."""

from __future__ import annotations

from ring.fastapp.config import get_config


def app_url(path: str) -> str:
    """Build an absolute URL into the web app.

    Emailed links have to use the scheme the app is actually served on. The
    frontend build bakes in an absolute API origin (`VITE_API_URL`), so a link
    on the wrong scheme drops the recipient on an origin where every API call
    is cross-origin and the CORS preflight is rejected.

    Args:
        path (str): Path within the app, with or without a leading slash

    Returns:
        str: Absolute URL, e.g. `https://ring.neilsriv.tech/loops/lttr_abc123`
    """
    base = get_config().APP_BASE_URL.rstrip("/")
    return f"{base}/{path.lstrip('/')}"
