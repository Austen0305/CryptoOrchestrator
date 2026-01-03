# MCP & Extensions Reference for User Rules

This document provides detailed information about available MCPs and extensions to include in User Rules.

---

## 📚 MCP (Model Context Protocol) Servers

### Quick Reference

**Total Configured:** 12 working MCP servers  
**Location:** `MCPs/` directory  
**Configuration:** `~/.cursor/mcp-hub.json`

### Core Services

#### 1. **filesystem** (14 tools)
**Use for:** All file operations  
**Server name:** `filesystem`

**Key Tools:**
- `read_text_file` - Read file contents
- `read_multiple_files` - Batch file reading
- `write_file` - Create/overwrite files
- `edit_file` - Make line-based edits
- `list_directory` - List files/folders
- `search_files` - Search files by pattern
- `directory_tree` - Recursive tree view

**When to use:**
- Instead of terminal `cat`, `ls`, `grep` commands
- When reading multiple files simultaneously
- For file operations in automation scripts

#### 2. **git** (27 tools)
**Use for:** All Git operations  
**Server name:** `git`

**Key Tools:**
- `git_status`, `git_diff`, `git_log`
- `git_add`, `git_commit`, `git_push`, `git_pull`
- `git_branch`, `git_checkout`, `git_merge`
- `git_stash`, `git_reset`, `git_blame`

**When to use:**
- Instead of terminal git commands
- For version control in AI workflows
- For understanding code history

#### 3. **context7** (2 tools)
**Use for:** Library documentation search  
**Server name:** `context7`  
**API Key:** Configured

**Key Tools:**
- `resolve-library-id` - Find library ID
- `search-documentation` - Search docs

**When to use:**
- Finding React, FastAPI, Python library docs
- Getting up-to-date API references
- Understanding library usage patterns

#### 4. **stackoverflow** (6 tools)
**Use for:** Finding solutions to common problems  
**Server name:** `stackoverflow`

**Key Tools:**
- `search_questions` - Search Stack Overflow
- `get_question_details` - Get question details

**When to use:**
- Common coding problems
- Error messages and solutions
- Best practice questions

#### 5. **brave-search** (2 tools)
**Use for:** Web search for current information  
**Server name:** `brave-search`  
**API Key:** Configured

**Key Tools:**
- `brave_web_search` - Web search

**When to use:**
- Current API documentation
- Latest best practices
- Troubleshooting guides
- Up-to-date information

#### 6. **coingecko** (Multiple tools)
**Use for:** Cryptocurrency price/data  
**Server name:** `coingecko`

**When to use:**
- Getting crypto prices
- Market data for trading features
- Token information

### Browser Automation

#### 7. **cursor-browser-extension** (18 tools)
**Use for:** Browser automation and testing  
**Server name:** `cursor-browser-extension` (direct call)

**Key Tools:**
- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Get accessibility snapshot (use first!)
- `browser_click` - Click elements
- `browser_type` - Type text
- `browser_take_screenshot` - Screenshots
- `browser_evaluate` - Execute JavaScript
- `browser_network_requests` - Monitor network

**Best Practices:**
- Always call `browser_snapshot` first to get element refs
- Use for E2E testing React components
- Test user flows and form submissions
- Monitor network requests for API debugging

#### 8. **puppeteer** (7 tools)
**Use for:** Alternative browser automation  
**Server name:** `puppeteer`

**When to use:**
- When cursor-browser-extension doesn't work
- For complex browser automation
- Headless browser testing

### AI & Knowledge

#### 9. **memory** (9 tools)
**Use for:** Knowledge graph storage  
**Server name:** `memory`

**Key Tools:**
- `create_entities` - Create knowledge entities
- `create_relations` - Link entities
- `search_nodes` - Search knowledge base
- `read_graph` - Read entire graph

**When to use:**
- Store project architecture decisions
- Link related concepts (e.g., "Authentication" → "JWT Tokens")
- Search for similar implementations
- Store design patterns and solutions

**Example Entities:**
- "Authentication System"
- "DEX Trading Flow"
- "Wallet Security Pattern"

#### 10. **sequential-thinking** (1 tool)
**Use for:** Complex problem solving  
**Server name:** `sequential-thinking`

**When to use:**
- Breaking down complex problems
- Planning multi-step features
- Architectural decisions
- Debugging complex issues

### Research

#### 11. **arxiv** (2 tools)
**Use for:** Academic paper search  
**Server name:** `arxiv`

**When to use:**
- Research on algorithms
- ML/AI model papers
- Technical research papers

#### 12. **allthingsdev** (6 tools)
**Use for:** API marketplace  
**Server name:** `allthingsdev`

**When to use:**
- Finding APIs and integrations
- API discovery

---

## 🛠️ Cursor Extensions

### Phase 1: Essential (16 extensions) - CRITICAL

#### Code Quality
- **Error Lens** (`usernamehw.errorlens`) - Inline error display
- **ESLint** (`dbaeumer.vscode-eslint`) - JavaScript/TypeScript linting
- **Prettier** (`esbenp.prettier-vscode`) - Code formatting
- **SonarLint** (`sonarsource.sonarlint-vscode`) - Code quality
- **Snyk** (`snyk.snyk-vscode`) - Security scanning

#### Python
- **Python** (`ms-python.python`) - Python support
- **Pylance** (`ms-python.vscode-pylance`) - Type checking (strict mode)
- **Black Formatter** (`ms-python.black-formatter`) - Formatting (88 chars)
- **Python Docstring Generator** (`njpwerner.autodocstring`)
- **Python Type Hint** (`njqdev.vscode-python-typehint`)
- **Python Test Explorer** (`littlefoxteam.vscode-python-test-adapter`)

#### Git
- **GitLens** (`eamodio.gitlens`) - Enhanced Git
- **Git Graph** (`mhutchie.vscode-git-graph`) - Visual history
- **Git History** (`donjayamanne.githistory`)
- **GitHub PR** (`github.vscode-pull-request-github`)

#### Utilities
- **DotEnv** (`mikestead.dotenv`) - .env file support

### Phase 2: Database & Testing (9 extensions) - HIGH

- **PostgreSQL** (`ms-ossdata.vscode-postgresql`)
- **SQLite Viewer** (`qwtel.sqlite-viewer`)
- **SQLite3 Editor** (`yy0931.sqlite3-editor`)
- **REST Client** (`humao.rest-client`) - API testing
- **RapidAPI Client** (`rapidapi.rapidapi-client`)
- **Coverage Gutters** (`ryanluker.vscode-coverage-gutters`)
- **Jest Runner** (`firsttris.vscode-jest-runner`)
- **YAML Support** (`redhat.vscode-yaml`)
- **YAML ❤️ JSON** (`daniel-hillmann.vscode-yaml-json`)

### Phase 3: Documentation & Productivity (12 extensions) - MEDIUM

- **Markdown All in One** (`yzhang.markdown-all-in-one`)
- **Markdown Preview Enhanced** (`shd101wyy.markdown-preview-enhanced`)
- **markdownlint** (`davidanson.vscode-markdownlint`)
- **Draw.io** (`hediet.vscode-drawio`)
- **Paste Image** (`mushan.vscode-paste-image`)
- **PlantUML** (`jebbs.plantuml`)
- **Better Comments** (`aaron-bond.better-comments`)
- **Path Intellisense** (`christian-kohler.path-intellisense`)
- **Import Cost** (`wix.vscode-import-cost`)
- **Todo Tree** (`gruntfuggly.todo-tree`)
- **Code Spell Checker** (`streetsidesoftware.code-spell-checker`)
- **Project Manager** (`alefragnani.project-manager`)

### Phase 4: Specialized Tools (17 extensions) - MEDIUM-LOW

- **Docker** (`ms-azuretools.vscode-docker`)
- **Kubernetes Tools** (`ms-kubernetes-tools.vscode-kubernetes-tools`)
- **Dev Containers** (`ms-vscode-remote.remote-containers`)
- **Live Server** (`ritwickdey.liveserver`)
- **Live Preview** (`ms-vscode.live-server`)
- **Auto Rename Tag** (`formulahendry.auto-rename-tag`)
- **ES7+ React snippets** (`dsznajder.es7-react-js-snippets`)
- **Indent Rainbow** (`oderwat.indent-rainbow`)
- **Dotenv Official** (`dotenv.dotenv-vscode`)
- **CodeMetrics** (`kisstkondoros.codemetrics`)
- **VS Code Lizard** (`brobeson.vscode-lizard`)
- **WakaTime** (`wakatime.vscode-wakatime`)
- **Pomodoro** (`mbparvezme.pomodoro-vscode-extension`)
- **Bookmarks** (`alefragnani.bookmarks`)
- **React Native Tools** (`msjsdiag.vscode-react-native`)
- **Expo Tools** (`expo.vscode-expo-tools`)
- **Electron Snippets** (`electron.electron-snippets`)

---

## 💡 Usage Guidelines for User Rules

### MCP Usage Rules

1. **Prefer MCPs over terminal commands** for file and git operations
2. **Search strategy**: Project files → context7 → stackoverflow → brave-search → arxiv
3. **Browser testing**: Use browser MCPs instead of manual testing
4. **Knowledge storage**: Use memory MCP for important patterns and decisions
5. **Complex problems**: Use sequential-thinking for multi-step solutions

### Extension Awareness Rules

1. **Check Error Lens** - Fix inline errors immediately
2. **Run ESLint** - Fix linting errors before committing
3. **Use Prettier** - Format code consistently (format on save)
4. **Review SonarLint/Snyk** - Address security and quality issues
5. **Use Coverage Gutters** - Maintain >85% test coverage
6. **Use GitLens** - Understand code history and blame

### Verification

Run `node scripts/utilities/verify-extensions.js` to check installed extensions.

---

**Last Updated:** December 30, 2025  
**For detailed docs:** See `MCPs/` directory in project
