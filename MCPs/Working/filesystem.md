# Filesystem MCP

**Status:** ✅ Working  
**Server:** filesystem  
**Tools:** 14 tools

## Available Tools

1. `read_file` - Read file contents (DEPRECATED, use read_text_file)
2. `read_text_file` - Read file contents with encoding support
3. `read_media_file` - Read image/audio files (base64)
4. `read_multiple_files` - Read multiple files simultaneously
5. `write_file` - Create/overwrite files
6. `edit_file` - Make line-based edits
7. `create_directory` - Create directories
8. `list_directory` - List files and directories
9. `list_directory_with_sizes` - List with file sizes
10. `directory_tree` - Recursive tree view (JSON)
11. `move_file` - Move/rename files
12. `search_files` - Search files by pattern
13. `get_file_info` - Get file metadata
14. `list_allowed_directories` - List accessible directories

## Usage Example

```json
{
  "serverName": "filesystem",
  "toolName": "list_allowed_directories",
  "toolArgs": {}
}
```

## Allowed Directories

- `C:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\Crypto-Orchestrator`

## Notes

- Only works within allowed directories
- Handles various text encodings
- Supports head/tail parameters for large files
