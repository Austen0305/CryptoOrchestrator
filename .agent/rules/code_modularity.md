---
trigger: always_on
glob: ["**/*.{py,ts,tsx}"]
description: Enforce modular code generation and clean entry points.
---

# Code Modularity Rule (2027)

Maintain a highly decoupled, composable architecture.

## 🧱 Functionality Isolation

- **Clean Entry Points**: Logic MUST NOT live in `main.py` or `App.tsx`. Use them only for routing/dependency injection.
- **Single Responsibility**: Every new file should handle exactly one domain responsibility (e.g., `gdpr_service.py` vs `auth_service.py`).
- **Shared Schemas**: All cross-boundary data transfers (Backend <-> Frontend) MUST use types defined in `shared/`.

## 🐍 Python Best Practices

- **Interface Abstraction**: Use Abstract Base Classes (ABCs) for services to allow easy swapping (e.g., swapping a production database for a mock).
- **Dependency Injection**: Use FastAPI's `Depends` to inject repositories and services.
- **Audit Hooks**: Expose `__init__.py` with clear public APIs.

## ⚛️ Frontend Best Practices (React 19)

- **Server-First Logic**: Prefer Server Components for data-heavy views to reduce client-side bundle size and PII exposure.
- **Component Isolation**: Extract complex UI logic into custom hooks (`client/src/hooks/`).
- **Atomic Components**: Build UI using small, reusable atoms that follow the `ui_modernization` standard.

---

// See also: [ui_modernization.md](file:///c:/Users/William%20Walker/Desktop/CryptoOrchestrator/.agent/workflows/ui_modernization.md)
