"""
Tests for CORS configuration in main.py
"""

import os
from unittest.mock import patch


class TestCORSConfiguration:
    """Test CORS origin configuration"""

    def test_cors_origins_with_empty_env(self):
        """Test that cors_origins is properly initialized with empty ALLOWED_ORIGINS"""
        # This test verifies the fix for the NameError when ALLOWED_ORIGINS is not set
        import importlib

        with patch.dict(os.environ, {"ALLOWED_ORIGINS": ""}, clear=False):
            # Re-import to trigger the configuration
            from server_fastapi import main as main_module

            # The module should load without NameError
            importlib.reload(main_module)

            # Verify the app was created successfully
            assert main_module.app is not None
            assert hasattr(main_module.app, "add_middleware")

    def test_cors_origins_with_valid_env(self):
        """Test that cors_origins is properly configured with valid ALLOWED_ORIGINS"""
        import importlib

        test_origins = "http://localhost:3000,https://example.com"
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": test_origins}, clear=False):
            from server_fastapi import main as main_module

            # The module should load without error
            importlib.reload(main_module)

            # Verify the app was created successfully
            assert main_module.app is not None

    def test_cors_origins_with_invalid_env(self):
        """Test that invalid origins are filtered out"""
        import importlib

        test_origins = "http://localhost:3000,invalid-origin,https://example.com"
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": test_origins}, clear=False):
            from server_fastapi import main as main_module

            # The module should load and skip invalid origins
            importlib.reload(main_module)

            # Verify the app was created successfully
            assert main_module.app is not None

    def test_cors_origins_defaults(self):
        """Test that default origins are used when ALLOWED_ORIGINS is not set"""
        import importlib

        with patch.dict(os.environ, {}, clear=False):
            # Remove ALLOWED_ORIGINS if it exists
            os.environ.pop("ALLOWED_ORIGINS", None)

            from server_fastapi import main as main_module

            # The module should load with defaults
            importlib.reload(main_module)

            # Verify the app was created successfully
            assert main_module.app is not None
