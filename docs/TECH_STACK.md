# CryptoOrchestrator Tech Stack

Detailed breakdown of the technology stack used in the CryptoOrchestrator platform.

## Backend Stack
- **Python 3.12** - Core language (upgraded for performance)
- **FastAPI** - High-performance backend (Python 3.12+)
- **SQLAlchemy 2.0+** - Async engine with structured migrations
- **PostgreSQL** - Production database with pgvector support
- **Redis** - High-speed caching, rate limiting, session storage, and Celery broker
- **Multi-Level Caching** - Memory + Redis caching with tag-based invalidation
- **Query Optimization** - Eager loading, pagination, N+1 prevention utilities
- **Response Optimization** - Pagination, field selection, null filtering, streaming
- **Celery** - Background task processing with prioritization and batching
- **Web3.py** - Blockchain interaction library
- **DEX Aggregators** - 0x, OKX, Rubic for best prices with fallback logic
- **OpenTelemetry** - Distributed tracing and monitoring
- **Idempotency** - Mandatory `idempotency_key` for all state-changing operations

## Frontend Stack
- **React 19+** - UI framework with Server Actions and memoization optimizations
- **TypeScript 5.x** - Type-safe JavaScript (strict mode)
- **Node 24.x** - Stable runtime for development and builds
- **Vite** - Fast build tool with advanced code splitting
- **TailwindCSS 4+** - Utility-first CSS with native cascade layers
- **shadcn/ui** - Premium UI components (Radix UI primitives)
- **TanStack Query v5** - Advanced data fetching, caching, and state management
- **WebSocket** - Real-time price and balance updates via Socket.io
- **PWA** - Progressive Web App support for mobile-like desktop experience

## Desktop Stack
- **Electron** - Cross-platform desktop app
- **Python Runtime Bundling** - Portable Python runtime bundled with app
- **Auto-updater** - Automatic update system with GitHub Releases
- **Code Signing** - Windows (PFX), macOS (Developer ID), Linux (GPG) support

## Mobile Stack
- **React Native** - Cross-platform mobile app
- **Expo** - Development tooling and build system
- **Push Notifications** - Expo push notifications with backend integration
- **Offline Mode** - Action queuing and data caching
- **Biometric Auth** - Face ID, Touch ID, fingerprint authentication

## Infrastructure & DevOps
- **Kubernetes** - Production-ready K8s manifests
- **Terraform** - Infrastructure as code for AWS
- **Docker Compose** - Multi-service orchestration
- **GitHub Actions** - Comprehensive CI/CD pipeline
- **Security Scanning** - Bandit, Safety, npm audit, Snyk, Semgrep, Trivy

## ML & Data
- **TensorFlow/Keras** - Deep learning
- **PyTorch** - ML Inference (1.26ms latency)
- **scikit-learn** - Machine learning utilities
- **pandas** - Data manipulation
- **numpy** - Numerical computing
