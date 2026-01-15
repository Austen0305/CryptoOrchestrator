---
trigger: always_on
glob: ["server_fastapi/**/*"]
description: Mandatory idempotency for financial operations.
---

# Financial Idempotency Rule

Ensure all balance-changing or state-critical operations in the backend are idempotent to prevent duplicate executions.

## Requirements
- **Idempotency Keys**: All POST/PUT requests involving wallets, trades, or payments must require an idempotency_key in the header or payload.
- **Transaction Manager**: Use server_fastapi.services.real_money_transaction_manager.py to wrap operations.
- **Deduplication**: Check for existing transaction IDs before executing side effects (e.g., blockchain broadcasts).
- **Atomic Operations**: Use SQLAlchemy async sessions to ensure atomicity. Rollback on any failure before committing.

## Audit Trails
- Log every attempted execution with the provided idempotency key.
- Store the result of successful idempotent operations to return the same response on retry.

