# MCP & Tools Quick Reference

**Quick lookup for recommended MCPs and VS Code extensions for CryptoOrchestrator**

## 🚀 Quick Install (Only 2 Extensions Needed!)

```powershell
# Install the 2 missing extensions
code --install-extension rangav.vscode-thunder-client
code --install-extension bradlc.vscode-tailwindcss

# Or use the installation script
powershell -ExecutionPolicy Bypass -File scripts/setup/install-recommended-extensions.ps1
```

## 📡 Current MCPs (17 Total)

### Most Valuable for Your Project

1. **api-tester** ⭐⭐⭐
   - Test FastAPI endpoints
   - Generate tests from OpenAPI spec
   - Load testing
   - **Use:** `docs/openapi.json` with this MCP

2. **context7** ⭐⭐⭐
   - FastAPI documentation
   - React/TypeScript docs
   - Web3.py documentation

3. **typescript-definition-finder** ⭐⭐
   - Find TypeScript definitions
   - Debug type issues

4. **coingecko** ⭐⭐
   - Real-time crypto prices
   - Market data

5. **memory** ⭐⭐
   - Store project knowledge
   - Remember patterns

## 🔌 Recommended Extensions Status

### ✅ Already Installed (12 Extensions)

| Extension | Status | Why |
|-----------|--------|----|
| Error Lens | ✅ Installed | Inline error display |
| Coverage Gutters | ✅ Installed | Visual test coverage |
| Path Intellisense | ✅ Installed | `@/*` import autocomplete |
| REST Client | ✅ Installed | API testing with .http files |
| Better Comments | ✅ Installed | Color-coded comments |
| Todo Tree | ✅ Installed | TODO management |
| Code Spell Checker | ✅ Installed | Typo detection |
| Markdown All in One | ✅ Installed | Markdown editing |
| Markdown Preview Enhanced | ✅ Installed | Markdown preview |
| SonarLint | ✅ Installed | Real-time code quality |
| Python Test Explorer | ✅ Installed | Pytest visual explorer |
| Jest Runner | ✅ Installed | Jest/Vitest runner |
| Import Cost | ✅ Installed | Bundle size impact |

### 🔥 Missing (2 Extensions - Install Now!)

| Extension | ID | Why |
|-----------|----|----|
| Thunder Client | `rangav.vscode-thunder-client` | API testing (Postman alternative) |
| Tailwind CSS | `bradlc.vscode-tailwindcss` | Tailwind autocomplete |

## 🎯 Usage Examples

### Using api-tester MCP

```json
{
  "serverName": "api-tester",
  "toolName": "ingest_spec",
  "toolArgs": {
    "file_path": "docs/openapi.json",
    "preferred_language": "python",
    "preferred_framework": "pytest"
  }
}
```

### Using context7 MCP

```json
{
  "serverName": "context7",
  "toolName": "resolve-library-id",
  "toolArgs": {
    "libraryName": "fastapi"
  }
}
```

## ✅ Verification

```powershell
# Check if extensions are installed
code --list-extensions | Select-String -Pattern "errorlens|coverage|thunder|sonarlint|tailwind"
```

## 📖 Full Documentation

See `docs/MCP_AND_TOOL_RECOMMENDATIONS.md` for complete details.
