# CryptoOrchestrator Tech Stack

Detailed breakdown of the technology stack used in the CryptoOrchestrator platform.

## Backend Stack
- **Python 3.12** - Core language (upgraded for performance)
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - ORM for database operations with eager loading
- **Alembic** - Database migrations with performance indexes and automated testing
- **PostgreSQL/SQLite** - Database options with optimized connection pooling
- **Redis** - Caching, rate limiting, and session storage
- **Multi-Level Caching** - Memory + Redis caching with tag-based invalidation
- **Query Optimization** - Eager loading, pagination, N+1 prevention utilities
- **Response Optimization** - Pagination, field selection, null filtering, streaming
- **Celery** - Background task processing with prioritization and batching
- **Web3.py** - Blockchain interaction library
- **DEX Aggregators** - 0x, OKX, Rubic for best prices with fallback logic
- **OpenTelemetry** - Distributed tracing and monitoring

## Frontend Stack
- **React 18+** - UI framework with memoization optimizations
- **TypeScript** - Type-safe JavaScript (strict mode)
- **Vite** - Fast build tool (37s builds) with advanced code splitting
- **TailwindCSS** - Utility-first CSS with custom components and animations
- **shadcn/ui** - Beautiful UI components (Radix UI primitives)
- **React Query** - Data fetching and caching with request deduplication
- **WebSocket** - Real-time price and balance updates
- **PWA** - Progressive Web App support

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
