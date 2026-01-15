---
name: premium_theming
description: UI/UX modernization skill for achieving premium aesthetics (glassmorphism, micro-animations).
---

# Premium Theming Skill

This skill provides guidelines and resources for modernizing the UI of CryptoOrchestrator to meet 2026 premium standards.

## Capabilities

- **Glassmorphism Design**: Implementing sophisticated backdrop-blur and translucent card systems.
- **Dynamic Theming**: Centralized CSS tokens for deep dark modes and high-contrast accessibility.
- **Micro-Animations**: Guidelines for buttery-smooth Framer Motion transitions and hover effects.

## Resources

- `resources/theme_tokens.css`: Core CSS variables for the project.
- `SKILL.md`: Design system documentation and implementation patterns.

## Implementation Guidelines

### 1. Glassmorphism Card Pattern
```css
.card-premium {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}
```

### 2. Micro-interactions
- Every interactive element must have a `hover` and `active` state defined.
- Entrance animations must use `y: 20, opacity: 0` to `y: 0, opacity: 1` transitions.
