"""
Enhanced API Documentation Middleware
Provides improved OpenAPI documentation with examples, schemas, and interactive features
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)


class EnhancedAPIDocumentation:
    """
    Enhanced API documentation generator
    
    Features:
    - Custom OpenAPI schema
    - Request/response examples
    - Error response documentation
    - API versioning info
    - Interactive examples
    - Code samples
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.custom_schemas: Dict[str, Any] = {}
        self.examples: Dict[str, List[Dict[str, Any]]] = {}
        self.code_samples: Dict[str, Dict[str, str]] = {}

    def add_example(
        self,
        endpoint: str,
        method: str,
        example: Dict[str, Any],
        description: Optional[str] = None,
    ):
        """Add example for endpoint"""
        key = f"{method.upper()} {endpoint}"
        if key not in self.examples:
            self.examples[key] = []

        self.examples[key].append({
            "description": description or "Example request",
            "value": example,
        })

    def add_code_sample(
        self,
        endpoint: str,
        method: str,
        language: str,
        code: str,
    ):
        """Add code sample for endpoint"""
        key = f"{method.upper()} {endpoint}"
        if key not in self.code_samples:
            self.code_samples[key] = {}

        self.code_samples[key][language] = code

    def generate_openapi_schema(self) -> Dict[str, Any]:
        """Generate enhanced OpenAPI schema"""
        # Get base schema
        schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description or "CryptoOrchestrator API",
            routes=self.app.routes,
        )

        # Add custom information
        schema["info"]["contact"] = {
            "name": "CryptoOrchestrator Support",
            "email": "support@cryptoorchestrator.com",
            "url": "https://docs.cryptoorchestrator.com",
        }

        schema["info"]["license"] = {
            "name": "Proprietary",
        }

        # Add servers
        schema["servers"] = [
            {
                "url": "http://localhost:8000",
                "description": "Development server",
            },
            {
                "url": "https://api.cryptoorchestrator.com",
                "description": "Production server",
            },
        ]

        # Add security schemes
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token authentication",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication",
            },
        }

        # Add examples to paths
        for path, methods in schema.get("paths", {}).items():
            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "patch", "delete"]:
                    key = f"{method.upper()} {path}"

                    # Add examples
                    if key in self.examples:
                        if "requestBody" in details:
                            details["requestBody"]["content"]["application/json"]["examples"] = {
                                f"example_{i}": ex for i, ex in enumerate(self.examples[key])
                            }
                        elif "parameters" in details:
                            # Add examples to parameters
                            for param in details["parameters"]:
                                if param.get("name") in [ex.get("name") for ex in self.examples[key]]:
                                    param["example"] = next(
                                        (ex["value"] for ex in self.examples[key] if ex.get("name") == param.get("name")),
                                        None
                                    )

                    # Add code samples as extension
                    if key in self.code_samples:
                        details["x-code-samples"] = self.code_samples[key]

                    # Add common response examples
                    if "responses" in details:
                        for status_code, response in details["responses"].items():
                            if status_code == "200" and "content" in response:
                                response["content"]["application/json"]["examples"] = {
                                    "success": {
                                        "summary": "Success response",
                                        "value": {
                                            "success": True,
                                            "data": {},
                                        },
                                    },
                                }
                            elif status_code in ["400", "401", "403", "404", "500"]:
                                if "content" in response:
                                    response["content"]["application/json"]["examples"] = {
                                        "error": {
                                            "summary": f"Error {status_code}",
                                            "value": {
                                                "success": False,
                                                "error": {
                                                    "code": status_code,
                                                    "message": self._get_error_message(status_code),
                                                },
                                            },
                                        },
                                    }

        # Add tags with descriptions
        schema["tags"] = [
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints",
            },
            {
                "name": "Bots",
                "description": "Trading bot management endpoints",
            },
            {
                "name": "Trades",
                "description": "Trade execution and management endpoints",
            },
            {
                "name": "Portfolio",
                "description": "Portfolio and balance management endpoints",
            },
            {
                "name": "Analytics",
                "description": "Analytics and reporting endpoints",
            },
            {
                "name": "Monitoring",
                "description": "System monitoring and health check endpoints",
            },
        ]

        return schema

    def _get_error_message(self, status_code: str) -> str:
        """Get default error message for status code"""
        messages = {
            "400": "Bad Request - Invalid input parameters",
            "401": "Unauthorized - Authentication required",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Resource does not exist",
            "500": "Internal Server Error - An unexpected error occurred",
        }
        return messages.get(status_code, "An error occurred")


def setup_enhanced_documentation(app: FastAPI) -> EnhancedAPIDocumentation:
    """Setup enhanced API documentation"""
    doc = EnhancedAPIDocumentation(app)

    # Add common examples
    doc.add_example(
        "/api/bots",
        "POST",
        {
            "name": "My Trading Bot",
            "strategy": "momentum",
            "initial_balance": 1000.0,
            "exchange": "binance",
        },
        description="Create a new trading bot",
    )

    doc.add_code_sample(
        "/api/bots",
        "POST",
        "python",
        """
import requests

response = requests.post(
    "http://localhost:8000/api/bots",
    json={
        "name": "My Trading Bot",
        "strategy": "momentum",
        "initial_balance": 1000.0,
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
print(response.json())
""",
    )

    doc.add_code_sample(
        "/api/bots",
        "POST",
        "javascript",
        """
const response = await fetch('http://localhost:8000/api/bots', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    name: 'My Trading Bot',
    strategy: 'momentum',
    initial_balance: 1000.0
  })
});

const data = await response.json();
console.log(data);
""",
    )

    # Override OpenAPI schema generation
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = doc.generate_openapi_schema()
        return app.openapi_schema

    app.openapi = custom_openapi

    logger.info("Enhanced API documentation configured")
    return doc

