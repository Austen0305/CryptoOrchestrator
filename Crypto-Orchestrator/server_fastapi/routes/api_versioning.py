"""
API Versioning Support
Allows multiple API versions for backward compatibility
"""

from fastapi import APIRouter, Request
from typing import Optional

# Version 1 Router
router_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

# Version 2 Router (future)
router_v2 = APIRouter(prefix="/api/v2", tags=["v2"])


@router_v1.get("/info")
async def api_v1_info():
    """API v1 information"""
    return {
        "version": "1.0.0",
        "status": "stable",
        "deprecated": False,
        "sunset_date": None,
        "documentation": "/docs",
        "features": [
            "Trading operations",
            "Market data",
            "Portfolio management",
            "Bot management",
            "Analytics",
        ],
    }


@router_v2.get("/info")
async def api_v2_info():
    """API v2 information"""
    return {
        "version": "2.0.0",
        "status": "beta",
        "deprecated": False,
        "sunset_date": None,
        "documentation": "/docs/v2",
        "features": [
            "Enhanced trading operations",
            "Real-time WebSocket streams",
            "Advanced analytics",
            "Multi-exchange support",
            "AI-powered predictions",
        ],
        "changes_from_v1": [
            "Improved response formats",
            "Better error handling",
            "Pagination support",
            "Rate limiting per endpoint",
        ],
    }


def get_api_version(request: Request) -> str:
    """
    Extract API version from request
    Supports both URL prefix and Accept header
    """
    path = request.url.path

    # Check URL prefix
    if "/api/v2" in path:
        return "2.0"
    elif "/api/v1" in path:
        return "1.0"

    # Check Accept header
    accept_header = request.headers.get("Accept", "")
    if "application/vnd.cryptoorchestrator.v2+json" in accept_header:
        return "2.0"

    # Default to v1
    return "1.0"


class VersionedResponse:
    """Helper class for version-specific responses"""

    @staticmethod
    def format_response_v1(data: dict) -> dict:
        """Format response for API v1"""
        return {
            "success": True,
            "data": data,
            "timestamp": None,  # v1 doesn't include timestamp
        }

    @staticmethod
    def format_response_v2(data: dict) -> dict:
        """Format response for API v2"""
        from datetime import datetime

        return {
            "success": True,
            "data": data,
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.0",
                "request_id": None,  # Would be set by middleware
            },
        }

    @staticmethod
    def format_error_v1(error: str, code: str) -> dict:
        """Format error for API v1"""
        return {"success": False, "error": error}

    @staticmethod
    def format_error_v2(error: str, code: str, details: Optional[dict] = None) -> dict:
        """Format error for API v2"""
        from datetime import datetime

        return {
            "success": False,
            "error": {
                "code": code,
                "message": error,
                "details": details or {},
                "timestamp": datetime.now().isoformat(),
            },
        }


# Example versioned endpoints
@router_v1.get("/markets/{symbol}")
async def get_market_data_v1(symbol: str):
    """Get market data - V1 format"""
    # Simplified response for v1
    return {"symbol": symbol, "price": 42000.0, "volume": 1234567.89}


@router_v2.get("/markets/{symbol}")
async def get_market_data_v2(symbol: str):
    """Get market data - V2 format with enhanced data"""
    from datetime import datetime

    # Enhanced response for v2
    return {
        "symbol": symbol,
        "price": {
            "current": 42000.0,
            "change_24h": 2.5,
            "change_24h_percent": 0.06,
            "high_24h": 43000.0,
            "low_24h": 41000.0,
        },
        "volume": {"base": 1234567.89, "quote": 51851850000.0},
        "market_cap": 820000000000.0,
        "timestamp": datetime.now().isoformat(),
        "source": "exchange_api",
    }
