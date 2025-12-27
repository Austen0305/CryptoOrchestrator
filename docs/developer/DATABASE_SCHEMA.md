# Database Schema Documentation

Auto-generated from SQLAlchemy models.

**Note**: This is a template. Run `scripts/generate_schema_docs.py` to generate the full documentation.

## Overview

CryptoOrchestrator uses PostgreSQL as the primary database with the following key tables:

- **User Management**: `users`, `sessions`, `api_keys`
- **Trading**: `bots`, `trades`, `orders`, `portfolios`
- **Marketplace**: `signal_providers`, `indicators`, `purchases`
- **Analytics**: `user_events`, `feature_usage`, `conversion_funnels`
- **Security**: `social_recovery_guardians`, `recovery_requests`
- **Accounting**: `accounting_connections`, `tax_transactions`

## Schema Generation

To generate the complete schema documentation:

```bash
python scripts/generate_schema_docs.py
```

This will inspect all SQLAlchemy models and generate comprehensive documentation.

## Key Relationships

### User → Bots → Trades
- Users can have multiple bots
- Bots can have multiple trades
- Trades reference orders and portfolios

### Marketplace Relationships
- Signal providers have ratings and subscribers
- Indicators have versions and purchases
- Users can purchase multiple items

### Analytics Relationships
- User events track user behavior
- Feature usage tracks feature adoption
- Conversion funnels track user journeys

## Migration Management

Database migrations are managed with Alembic:

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Indexes

Key indexes for performance:
- User lookups: `idx_bots_user_id`
- Time-based queries: `idx_trades_created_at`
- Status filtering: `idx_orders_status`
- Analytics queries: `idx_user_events_user_time`

## Additional Resources

- [Alembic Migrations](../alembic/versions/)
- [Model Definitions](../../server_fastapi/models/)
- [Database Configuration](../../server_fastapi/database/)
