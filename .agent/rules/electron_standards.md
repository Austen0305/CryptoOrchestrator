Priority: LOW
Scope: FULL
Overrides: NONE

---
trigger: always_on
glob: "electron/**/*"
description: Standards for Electron desktop application.
---

# Electron Standards

## Security first
- **Context Isolation**: Always enable `contextIsolation: true` in `webPreferences`.
- **Sandbox**: Enable `sandbox: true` where possible.
- **IPC Communication**: Use a `preload.js` script with `contextBridge` to expose specific APIs to the renderer. Never expose `ipcRenderer` directly.

## Process Management
- Handle `window-all-closed` and `activate` events properly for cross-platform support.
- Use `utilityProcess` for heavy background tasks to keep the main process responsive.

