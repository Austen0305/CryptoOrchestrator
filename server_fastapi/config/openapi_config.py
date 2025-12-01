"""
OpenAPI/Swagger Documentation Configuration
Enhanced API documentation with examples and better descriptions
"""
from typing import Dict, Any
import os

def get_openapi_config() -> Dict[str, Any]:
    """Get enhanced OpenAPI configuration"""
    
    # Get environment info
    environment = os.getenv("NODE_ENV", "development")
    version = os.getenv("API_VERSION", "1.0.0")
    
    # Base OpenAPI info
    openapi_config = {
        "title": "CryptoOrchestrator API",
        "version": version,
        "description": """
## Professional AI-Powered Cryptocurrency Trading Platform API

CryptoOrchestrator is an enterprise-grade trading automation platform featuring:

### 🚀 Core Features
- **AI-Powered Trading**: Machine learning models for market predictions
- **Multi-Exchange Support**: Trade across 5+ major exchanges
- **Advanced Risk Management**: Comprehensive risk controls and monitoring
- **Real-Time Analytics**: Live market data and portfolio tracking
- **Automated Trading Bots**: Create and manage trading bots
- **Backtesting**: Test strategies with historical data

### 🔒 Security
- **JWT Authentication**: Secure token-based authentication
- **2FA Support**: Two-factor authentication for sensitive operations
- **KYC Verification**: Know Your Customer compliance
- **Cold Storage**: High-value asset protection
- **Rate Limiting**: DDoS protection and fair usage

### 💰 Monetization
- **Wallet System**: Multi-currency wallet with deposits/withdrawals
- **Staking Rewards**: Earn passive income (2-18% APY)
- **Payment Processing**: Stripe integration for fiat deposits
- **Subscription Tiers**: Free, Basic, Pro, Enterprise plans

### 📊 Observability
- **Request Tracking**: Unique request IDs for tracing
- **Health Checks**: Kubernetes-ready liveness/readiness probes
- **Query Monitoring**: Database performance insights
- **Metrics**: Prometheus metrics endpoint

### 🔧 Technical Details
- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: React 18+ with TypeScript
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis (optional, with in-memory fallback)
- **Real-time**: WebSocket support for live updates

### 📚 Getting Started

1. **Authentication**: Register and get JWT token
2. **API Keys**: Add exchange API keys for trading
3. **Create Bot**: Set up your first trading bot
4. **Monitor**: Track performance and adjust strategies

### 🔗 Links
- [GitHub Repository](https://github.com/cryptoorchestrator)
- [Documentation](https://docs.cryptoorchestrator.com)
- [Support](https://support.cryptoorchestrator.com)
        """,
        "terms_of_service": "https://cryptoorchestrator.com/terms",
        "contact": {
            "name": "CryptoOrchestrator Support",
            "email": "support@cryptoorchestrator.com",
            "url": "https://support.cryptoorchestrator.com"
        },
        "license_info": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.cryptoorchestrator.com",
                "description": "Production server"
            }
        ],
        "tags": [
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints"
            },
            {
                "name": "Trading",
                "description": "Trading operations, orders, and execution"
            },
            {
                "name": "Bots",
                "description": "Trading bot management and configuration"
            },
            {
                "name": "Portfolio",
                "description": "Portfolio tracking and analytics"
            },
            {
                "name": "Wallet",
                "description": "Wallet management, deposits, and withdrawals"
            },
            {
                "name": "Staking",
                "description": "Staking rewards and management"
            },
            {
                "name": "Cold Storage",
                "description": "Cold storage transfers for high-value assets"
            },
            {
                "name": "Health",
                "description": "Health checks and system status"
            },
            {
                "name": "Query Optimization",
                "description": "Database query optimization and monitoring"
            },
            {
                "name": "Cache Warmer",
                "description": "Cache warming and management"
            }
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token obtained from /api/auth/login"
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for programmatic access"
                }
            }
        }
    }
    
    # Add environment-specific info
    if environment == "production":
        openapi_config["servers"] = [
            {
                "url": "https://api.cryptoorchestrator.com",
                "description": "Production server"
            }
        ]
    else:
        openapi_config["servers"] = [
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ]
    
    return openapi_config


def custom_openapi(app) -> Dict[str, Any]:
    """Custom OpenAPI schema generator with enhancements"""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom enhancements
    config = get_openapi_config()
    
    # Update schema with custom config
    openapi_schema["info"].update({
        "description": config["description"],
        "termsOfService": config.get("terms_of_service"),
        "contact": config.get("contact"),
        "license": config.get("license_info")
    })
    
    # Add servers
    if "servers" in config:
        openapi_schema["servers"] = config["servers"]
    
    # Add tags
    if "tags" in config:
        openapi_schema["tags"] = config["tags"]
    
    # Add security schemes
    if "components" in config and "securitySchemes" in config["components"]:
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}
        openapi_schema["components"]["securitySchemes"].update(
            config["components"]["securitySchemes"]
        )
    
    app.openapi_schema = openapi_schema
    return openapi_schema

