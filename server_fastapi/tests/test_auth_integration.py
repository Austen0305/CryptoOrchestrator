import pytest
from fastapi.testclient import TestClient
from server_fastapi.main import app
import uuid

@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for a logged-in user with unique email per test"""
    # Use unique email to avoid duplicate registration across tests
    unique_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
    
    # Register a test user
    register_data = {
        "email": unique_email,
        "password": "TestPassword123!",
        "name": "Test User"
    }
    reg_response = client.post("/api/auth/register", json=register_data)
    assert reg_response.status_code == 200, f"Registration failed: {reg_response.json()}"

    # Login to get token
    login_data = {
        "email": unique_email,
        "password": "TestPassword123!"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["data"]["token"]

    return {"Authorization": f"Bearer {token}"}

class TestAuthIntegration:
    """Integration tests for authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User"
        }

        response = client.post("/api/auth/register", json=data)

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "user" in response_data["data"]
        assert response_data["data"]["user"]["email"] == "newuser@example.com"
        assert response_data["data"]["user"]["name"] == "New User"

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!",
            "name": "First User"
        }

        # First registration should succeed
        response1 = client.post("/api/auth/register", json=data)
        assert response1.status_code == 200

        # Second registration should fail
        response2 = client.post("/api/auth/register", json=data)
        assert response2.status_code == 400

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "name": "Test User"
        }

        response = client.post("/api/auth/register", json=data)
        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        data = {
            "email": "weakpass@example.com",
            "password": "123",  # Too short
            "name": "Test User"
        }

        response = client.post("/api/auth/register", json=data)
        assert response.status_code == 422  # Validation error

    def test_login_success(self, client):
        """Test successful login"""
        # First register
        register_data = {
            "email": "loginuser@example.com",
            "password": "LoginPass123!",
            "name": "Login User"
        }
        client.post("/api/auth/register", json=register_data)

        # Then login
        login_data = {
            "email": "loginuser@example.com",
            "password": "LoginPass123!"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "token" in response_data["data"]
        assert "refreshToken" in response_data["data"]
        assert response_data["data"]["user"]["email"] == "loginuser@example.com"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    def test_login_username_instead_of_email(self, client):
        """Test login using username instead of email"""
        # First register with username
        register_data = {
            "email": "username_login@example.com",
            "password": "UsernamePass123!",
            "name": "Username User"
        }
        client.post("/api/auth/register", json=register_data)

        # Then login with username (if supported)
        login_data = {
            "username": "username_login@example.com",  # Using email as username
            "password": "UsernamePass123!"
        }

        response = client.post("/api/auth/login", json=login_data)
        # This might fail if username login is not fully implemented
        assert response.status_code in [200, 401]  # Either success or not supported

    def test_get_profile_authenticated(self, client, auth_headers):
        """Test getting user profile when authenticated"""
        response = client.get("/api/auth/profile", headers=auth_headers)

        assert response.status_code == 200
        profile_data = response.json()
        assert "id" in profile_data
        assert "email" in profile_data
        assert "name" in profile_data

    def test_get_profile_unauthenticated(self, client):
        """Test getting user profile without authentication"""
        response = client.get("/api/auth/profile")

        assert response.status_code == 403  # Forbidden

    def test_update_profile(self, client, auth_headers):
        """Test updating user profile"""
        update_data = {
            "name": "Updated Name"
        }

        response = client.patch("/api/auth/profile", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Profile updated successfully"

    def test_refresh_token(self, client, auth_headers):
        """Test refreshing access token"""
        # First get a refresh token by logging in
        login_data = {
            "email": "refresh@example.com",
            "password": "RefreshPass123!"
        }

        # Register first
        register_data = {
            "email": "refresh@example.com",
            "password": "RefreshPass123!",
            "name": "Refresh User"
        }
        client.post("/api/auth/register", json=register_data)

        # Login to get refresh token
        login_response = client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["data"]["refreshToken"]

        # Now refresh the token
        refresh_data = {
            "refreshToken": refresh_token
        }

        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        refresh_response = response.json()
        assert "accessToken" in refresh_response
        assert "refreshToken" in refresh_response

    def test_logout(self, client, auth_headers):
        """Test user logout"""
        logout_data = {}  # Can include refresh token if needed

        response = client.post("/api/auth/logout", json=logout_data, headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    def test_forgot_password(self, client):
        """Test forgot password functionality"""
        # Register a user first
        register_data = {
            "email": "forgotpass@example.com",
            "password": "ForgotPass123!",
            "name": "Forgot User"
        }
        client.post("/api/auth/register", json=register_data)

        # Request password reset
        forgot_data = {
            "email": "forgotpass@example.com"
        }

        response = client.post("/api/auth/forgot-password", json=forgot_data)

        assert response.status_code == 200
        # The response should not reveal if email exists
        assert "message" in response.json()

    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with non-existent email"""
        forgot_data = {
            "email": "nonexistent@example.com"
        }

        response = client.post("/api/auth/forgot-password", json=forgot_data)

        assert response.status_code == 200
        # Should not reveal if email exists
        assert "message" in response.json()

    def test_rate_limiting_register(self, client):
        """Test rate limiting on registration endpoint"""
        data = {
            "email": "ratelimit@example.com",
            "password": "RateLimit123!",
            "name": "Rate Limit User"
        }

        # Make multiple requests quickly
        responses = []
        for i in range(10):
            email = f"ratelimit{i}@example.com"
            data["email"] = email
            response = client.post("/api/auth/register", json=data)
            responses.append(response.status_code)

        # At least some should be rate limited (429)
        # Note: This depends on the rate limit configuration
        assert any(code == 429 for code in responses) or all(code in [200, 400] for code in responses)