---
trigger: always_on
glob: "**/*.{py,ts,tsx}"
description: Enforce modular code generation and clean entry points.
---

# Code Modularity Rule

Follow these standards to ensure the codebase remains maintainable and modular.

## Functionality Isolation
- **No Logic in Entry Points**: Do not implement business logic directly in `main.py` or `App.tsx`. 
- **Distinct Files**: Generate distinct functionality in new, descriptive files (e.g., `feature_x.py` or `useFeatureX.ts`).
- **Example Methods**: When showcasing new functionality, create an `example_feature_x` method in the entry point that simply calls the new module.

## Python Specifics
- Use `__init__.py` to expose clean public APIs for directories.
- Avoid circular imports by using interface-based design or abstraction layers.

## Frontend Specifics
- Extract complex UI components into their own files in `src/components/`.
- Extract complex business logic into custom hooks in `src/hooks/`.
