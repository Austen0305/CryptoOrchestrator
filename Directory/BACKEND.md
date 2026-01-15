# Backend Directory Map (server_fastapi/)

The backend is a FastAPI-based high-frequency trading and orchestration API.

## 🏗️ Core Architecture

### [App Lifecycle](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/core/lifecycle.py)
Handles startup/shutdown of database pools, background workers, and service bootstrapping.

### [Router Discovery](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/core/router_discovery.py)
Implements a 2026 specialization for automatic mounting of routes based on directory structure.

## 🛠️ Service Layer (`server_fastapi/services/`)

| Feature | Key Service File |
| :--- | :--- |
| **Trading** | [trading_orchestrator.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/trading/trading_orchestrator.py) |
| **Risk** | [advanced_risk_manager.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/advanced_risk_manager.py) |
| **Audit** | [audit_log_service.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/audit_log_service.py) |
| **Transactions** | [real_money_transaction_manager.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/real_money_transaction_manager.py) |
| **Auth** | [auth/service.py](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/services/auth/service.py) |

## 📦 Data Layer

- **Models:** [server_fastapi/models/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/models/)
- **Repositories:** [server_fastapi/repositories/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/repositories/)
- **Migrations:** [alembic/versions/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/alembic/versions/)

## 🕒 Background Tasks

- **Worker:** [server_fastapi/workers/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/workers/)
- **Tasks:** [server_fastapi/celery_tasks/](file:///C:/Users/William%20Walker/Desktop/CryptoOrchestrator/server_fastapi/celery_tasks/)
