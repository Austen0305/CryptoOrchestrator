---
trigger: always_on
glob: "client/src/**/*"
description: Standards for React hooks and API integration.
---

# Frontend Hook Standards

Maintain consistency and performance in data fetching and state management.

## Requirements
- **Custom Hooks**: Isolate all TanStack Query logic into custom hooks in client/src/hooks/.
- **Error Handling**: Every hook must expose rror and isLoading states. Use alidation.ts for response integrity.
- **Cache Policy**: Use the centralized queryClient.ts settings. Avoid ad-hoc cache overrides unless justified.
- **Types**: Use strict TypeScript interfaces for all hook inputs and outputs. Link to client/src/types/.

## Aesthetics
- Use LoadingSkeleton or shimmer effects when isLoading is true.
- Trigger success/error toasts for all mutations.
