# Safety & Compliance Directory Map

**URGENT CAUTION:** This platform handles real-money financial transactions. All logic identified in this map is critical to system integrity and must not be bypassed.

## 🛡️ Financial Safety Guards

### [Risk Manager](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/advanced_risk_manager.py)
Central authority for pre-trade risk checks, capital limits, and circuit breakers.

### [Transaction Idempotency](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/real_money_transaction_manager.py)
Ensures that financial operations (deposits, trades, withdrawals) are executed exactly once.

### [Regulatory Filter Middleware](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/middleware/regulatory_filter.py)
Enforces regional restrictions and compliance checks (e.g., UK 2026 tax reporting).

## 📜 Compliance & Auditing

### [Compliance Services](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/compliance/)
Contains logic for KYC, AML, and GDPR data handling.

### [Immutable Audit Trails](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/audit/)
Handles logging of all sensitive state changes. Logs are designed for SOC2/GDPR alignment.

## 🚩 Security Logic

- **Encryption:** [encryption_service.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/encryption_service.py)
- **Wallet Signatures:** [wallet_signature_service.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/wallet_signature_service.py)
- **Secret Rotation:** [secret_rotation.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/secret_rotation.py)
