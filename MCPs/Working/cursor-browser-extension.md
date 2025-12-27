# Cursor Browser Extension MCP

**Status:** ✅ Working  
**Server:** cursor-browser-extension  
**Tools:** 18 tools

## Available Tools

### Navigation
- `browser_navigate` - Navigate to URL
- `browser_navigate_back` - Go back
- `browser_tabs` - Manage tabs

### Interaction
- `browser_click` - Click element
- `browser_type` - Type text
- `browser_hover` - Hover element
- `browser_drag` - Drag and drop
- `browser_select_option` - Select dropdown
- `browser_fill_form` - Fill multiple fields
- `browser_press_key` - Press keyboard key

### Information
- `browser_snapshot` - Get accessibility snapshot
- `browser_take_screenshot` - Take screenshot
- `browser_evaluate` - Execute JavaScript
- `browser_console_messages` - Get console messages
- `browser_network_requests` - Get network requests

### Utilities
- `browser_wait_for` - Wait for conditions
- `browser_resize` - Resize window
- `browser_handle_dialog` - Handle dialogs

## Usage Example

```json
{
  "serverName": "cursor-browser-extension",
  "toolName": "browser_navigate",
  "toolArgs": {
    "url": "https://example.com"
  }
}
```

## Features

- Full browser automation
- Accessibility snapshots for element refs
- Screenshot capabilities
- Network monitoring
- Console message access
- Form automation

## Notes

- Use `browser_snapshot` to get element refs for interactions
- Supports multiple tabs
- Can handle dialogs and alerts
- Network request monitoring available
