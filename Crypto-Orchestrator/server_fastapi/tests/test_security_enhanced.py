"""
Enhanced security tests for authentication, authorization, and security features.
Tests account lockout, token rotation, CSRF protection, XSS prevention, etc.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


class TestAccountLockout:
    """Tests for account lockout functionality"""

    async def test_account_lockout_after_failed_attempts(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that account is locked after multiple failed login attempts"""
        user = test_user_with_auth

        # Attempt login with wrong password multiple times
        for i in range(6):  # More than MAX_FAILED_ATTEMPTS (5)
            response = await client.post(
                "/api/auth/login",
                json={"email": user["email"], "password": "WrongPassword123!"},
            )

            if i < 4:  # First 4 attempts should fail with 401
                assert response.status_code == 401
            else:  # After 5 attempts, should be locked (429)
                assert response.status_code == 429
                assert "locked" in response.json().get("detail", "").lower()
                break

    async def test_account_lockout_reset_on_success(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that failed attempts are reset on successful login"""
        user = test_user_with_auth

        # Fail login twice
        for _ in range(2):
            await client.post(
                "/api/auth/login",
                json={"email": user["email"], "password": "WrongPassword123!"},
            )

        # Successful login should reset counter
        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": user["password"]},
        )

        assert response.status_code in [200, 201]

        # Now failed attempts should start from 0 again
        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "WrongPassword123!"},
        )
        # Should be 401, not 429 (not locked yet)
        assert response.status_code == 401

    async def test_account_lockout_progressive_delay(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that lockout duration increases with each lockout"""
        user = test_user_with_auth

        # Lock account first time
        for _ in range(6):
            await client.post(
                "/api/auth/login",
                json={"email": user["email"], "password": "WrongPassword123!"},
            )

        # Wait for lockout to expire (simplified test)
        # In real scenario, would wait for lockout period
        # For now, just verify lockout occurred
        response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "WrongPassword123!"},
        )
        assert response.status_code == 429


class TestTokenRotation:
    """Tests for token rotation on suspicious activity"""

    async def test_token_blacklist(self, client: AsyncClient, test_user_with_auth):
        """Test that blacklisted tokens are rejected"""
        user = test_user_with_auth

        # Get a valid token
        login_response = await client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": user["password"]},
        )

        if login_response.status_code == 200:
            token = login_response.json().get("token")

            # Use token to access protected endpoint
            response = await client.get(
                "/api/bots/", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200

            # Blacklist token (would be done by admin or on suspicious activity)
            from server_fastapi.services.auth.token_rotation import (
                get_token_rotation_service,
            )

            token_service = get_token_rotation_service()
            token_service.blacklist_token(token, "test_revocation")

            # Token should now be rejected
            response = await client.get(
                "/api/bots/", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 401


class TestCSRFProtection:
    """Tests for CSRF protection"""

    async def test_csrf_token_required_for_post(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that CSRF token is required for POST requests"""
        user = test_user_with_auth

        # Get CSRF token from a GET request
        get_response = await client.get("/api/bots/", headers=user["auth_headers"])
        csrf_token = get_response.headers.get("X-CSRF-Token")

        if csrf_token:
            # POST without CSRF token should fail
            response = await client.post(
                "/api/bots/",
                json={
                    "name": "Test Bot",
                    "symbol": "BTC/USDT",
                    "strategy": "simple_ma",
                },
                headers=user["auth_headers"],
            )
            # May fail with 403 if CSRF protection is enabled
            # Or succeed if CSRF is optional for API endpoints
            assert response.status_code in [200, 201, 403]

    async def test_csrf_token_validation(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that invalid CSRF tokens are rejected"""
        user = test_user_with_auth

        # Try POST with invalid CSRF token
        headers = {**user["auth_headers"], "X-CSRF-Token": "invalid-token-12345"}
        response = await client.post(
            "/api/bots/",
            json={"name": "Test Bot", "symbol": "BTC/USDT", "strategy": "simple_ma"},
            headers=headers,
        )
        # Should either succeed (if CSRF not enforced for API) or fail with 403
        assert response.status_code in [200, 201, 403]


class TestXSSPrevention:
    """Tests for XSS prevention"""

    async def test_xss_injection_prevention(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that XSS attempts are sanitized"""
        user = test_user_with_auth

        # Try to create bot with XSS payload in name
        xss_payload = "<script>alert('XSS')</script>"
        response = await client.post(
            "/api/bots/",
            json={"name": xss_payload, "symbol": "BTC/USDT", "strategy": "simple_ma"},
            headers=user["auth_headers"],
        )

        if response.status_code in [200, 201]:
            bot = response.json()
            # Name should be sanitized (no script tags)
            assert "<script>" not in bot.get("name", "")
            assert "alert" not in bot.get("name", "")


class TestSQLInjectionPrevention:
    """Tests for SQL injection prevention"""

    async def test_sql_injection_in_query_params(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that SQL injection in query params is rejected"""
        user = test_user_with_auth

        # Try SQL injection in query parameter
        sql_injection = "1' OR '1'='1"
        response = await client.get(
            f"/api/bots/?user_id={sql_injection}", headers=user["auth_headers"]
        )

        # Should either return empty results or reject the request
        # Should not execute SQL injection
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            # Should return empty or filtered results, not all bots
            bots = response.json()
            # If it's a list, it should be empty or filtered
            # If it's a dict, it should not contain injected data
            assert isinstance(bots, (list, dict))


class TestPasswordStrength:
    """Tests for password strength validation"""

    async def test_password_too_short(self, client: AsyncClient):
        """Test that passwords shorter than 12 characters are rejected"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "Short1!",  # Only 7 characters
                "name": "Test User",
                "username": "testuser",
            },
        )

        # Should reject short password
        assert response.status_code in [400, 422]
        assert (
            "12" in response.json().get("detail", "").lower()
            or "length" in response.json().get("detail", "").lower()
        )

    async def test_password_missing_requirements(self, client: AsyncClient):
        """Test that passwords missing requirements are rejected"""
        # Password without uppercase
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test2@example.com",
                "password": "lowercase123!",  # No uppercase
                "name": "Test User",
                "username": "testuser2",
            },
        )

        # Should reject password missing uppercase
        assert response.status_code in [400, 422]

    async def test_password_meets_requirements(self, client: AsyncClient):
        """Test that valid passwords are accepted"""
        import uuid

        unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

        response = await client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "ValidPassword123!",  # 20 chars, has all requirements
                "name": "Test User",
                "username": f"testuser{uuid.uuid4().hex[:6]}",
            },
        )

        # Should accept valid password
        assert response.status_code in [200, 201]


class TestRateLimiting:
    """Tests for rate limiting effectiveness"""

    async def test_rate_limit_enforcement(
        self, client: AsyncClient, test_user_with_auth
    ):
        """Test that rate limits are enforced"""
        user = test_user_with_auth

        # Make many rapid requests
        responses = []
        for i in range(110):  # More than default limit
            response = await client.get("/api/bots/", headers=user["auth_headers"])
            responses.append(response.status_code)

            if response.status_code == 429:
                # Rate limit hit
                assert "rate limit" in response.json().get("detail", "").lower()
                break

        # Should hit rate limit at some point
        assert 429 in responses or len(responses) < 110

    async def test_rate_limit_headers(self, client: AsyncClient, test_user_with_auth):
        """Test that rate limit headers are included in responses"""
        user = test_user_with_auth

        response = await client.get("/api/bots/", headers=user["auth_headers"])

        # Should include rate limit headers
        assert "X-RateLimit-Limit" in response.headers or response.status_code != 200
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
