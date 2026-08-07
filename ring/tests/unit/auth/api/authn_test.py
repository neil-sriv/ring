"""Tests for authentication API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuthnAPI:
    """Test suite for login / authn API endpoints."""

    def test_deprecated_endpoints_return_501(
        self, unauthenticated_client: TestClient
    ) -> None:
        """Deprecated auth endpoints should return 501, not an unhandled 500."""
        cases = [
            ("post", "/login/test-token"),
            ("post", "/password-recovery-html-content/test@example.com"),
        ]
        for method, path in cases:
            response = getattr(unauthenticated_client, method)(path)
            assert response.status_code == 501, path
            assert (
                response.json()["detail"]
                == "This endpoint is deprecated and not implemented"
            )
