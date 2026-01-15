Priority: LOW
Scope: FULL
Overrides: NONE

---
trigger: always_on
glob: ["mobile/**/*"]
description: Standards for React Native / Expo mobile application.
---

# Mobile (Expo) Standards

## Component Architecture
- Place reusable UI components in src/components/.
- Use functional components with hooks exclusively.
- Types and interfaces must reside in src/types/.

## Styling & Performance
- Use StyleSheet.create for optimized styling.
- Avoid large inline objects in render to prevent unnecessary re-renders.
- Use FlashList for long lists to ensure 60fps performance.

## Expo Workflow
- Keep pp.json updated with correct versioning and permissions.
- Use xpo-constants for environment-specific configuration.

