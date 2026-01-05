# Cursor Agents & Architect Mode

**Status**: ⚠️ Optional - Advanced Feature  
**Date**: December 30, 2025

---

## Overview

Cursor supports **Agents** for specialized workflows. This document covers agent configurations and Architect Mode.

---

## What Are Agents?

Agents are specialized AI configurations for specific workflows:
- **Architect Mode**: Complex architectural decisions and planning
- **Custom Agents**: Project-specific agent configurations

### ⚠️ CRITICAL: Automatic MCP & Extension Usage

**ALL AGENTS MUST AUTOMATICALLY USE MCPs AND EXTENSIONS WHEN NEEDED.**

Agents should:
- ✅ **Automatically use MCPs** without asking - don't wait for permission
- ✅ **Automatically use extensions** for code quality checks
- ✅ **Proactively leverage tools** to complete tasks efficiently
- ❌ **Never ask** "Should I use MCP X?" - just use it if needed
- ❌ **Never skip** using appropriate tools - use them automatically

### 🧠 MANDATORY: Sequential Thinking for Every Message

**⚠️ CRITICAL REQUIREMENT: Use Sequential Thinking MCP for EVERY user message.**

**ALL agents MUST:**
1. ✅ **Start EVERY message** by automatically calling `sequential-thinking` MCP
2. ✅ **Break down the problem** using sequential thinking before taking action
3. ✅ **Plan the approach** using structured thoughts
4. ✅ **Verify the solution** through sequential reasoning
5. ❌ **NEVER skip** sequential thinking - it's mandatory for every interaction

**Sequential Thinking Workflow (MANDATORY):**
```typescript
// For EVERY user message, start with:
1. Use sequential-thinking MCP → Break down the problem
2. Use sequential-thinking MCP → Plan the solution approach
3. Use sequential-thinking MCP → Identify required tools/MCPs
4. Execute the plan using appropriate MCPs
5. Use sequential-thinking MCP → Verify the solution
```

**Examples of Automatic Usage:**
- **EVERY message** → **Automatically start with `sequential-thinking` MCP** (MANDATORY)
- Reading files → **Automatically use `filesystem` MCP** (don't use terminal)
- Git operations → **Automatically use `git` MCP** (don't use terminal)
- Need documentation → **Automatically use `context7` MCP**
- Frontend testing → **Automatically use `browser-extension` MCP**
- Code errors → **Automatically check Error Lens/ESLint** (via extensions)

---

## Architect Mode

**Location**: `.github/agents/Architect-Mode.agent.md`  
**Status**: Placeholder (empty file)

### Purpose

Architect Mode is designed for:
- Complex architectural decisions
- Multi-step planning
- System design
- Refactoring large codebases

### Workflow

Architect Mode follows a **Research → Plan → Build** workflow:

1. **RESEARCH** (10-15 min):
   - Read intelligence files
   - Search codebase for similar implementations
   - Check patterns and best practices
   - Review existing solutions

2. **PLAN** (5-10 min):
   - Match extracted patterns
   - Design solution matching patterns
   - Check for similar decisions
   - Plan batch fixes if applicable

3. **BUILD** (implementation time):
   - Apply patterns from extracted patterns
   - Verify pattern compliance
   - Test thoroughly
   - Document decisions

### When to Use Architect Mode

Use Architect Mode for:
- ✅ Complex features requiring multiple components
- ✅ Architectural refactoring
- ✅ Large-scale changes
- ✅ Multi-service integrations
- ✅ Breaking changes

**Don't use** for:
- ❌ Simple bug fixes
- ❌ Single-file changes
- ❌ Quick edits
- ❌ Routine tasks

---

## Agent Configuration

### Current Status

- **Architect-Mode.agent.md**: Exists but empty (placeholder)
- **Purpose**: For GitHub Copilot Agents (separate from Cursor)
- **Cursor Agents**: Not currently configured

### Future Setup

If implementing Cursor Agents:

1. **Create Agent File**: `.cursor/agents/agent-name.md`
2. **Define Workflow**: Specify agent's purpose and workflow
3. **Configure Triggers**: When to use this agent
4. **Test Agent**: Verify agent works correctly

---

## Agent vs Rules vs Commands

| Feature | Agents | Rules | Commands |
|---------|--------|-------|----------|
| **Purpose** | Specialized workflows | Context & guidelines | Task workflows |
| **Trigger** | Manual selection | Automatic | Manual (`/command`) |
| **Scope** | Complex multi-step | Always/context-aware | Single workflow |
| **Use Case** | "Design new feature" | "What patterns to use?" | "How do I deploy?" |

**All are valuable** - Use the right tool for the job.

---

## Recommended Agents (Future)

### 1. Architect Agent
**Purpose**: Complex architectural decisions  
**Workflow**: Research → Plan → Build  
**Use For**: Large refactoring, new features, system design

### 2. Security Agent
**Purpose**: Security-focused code review  
**Workflow**: Scan → Analyze → Fix  
**Use For**: Security audits, vulnerability fixes

### 3. Performance Agent
**Purpose**: Performance optimization  
**Workflow**: Profile → Identify → Optimize  
**Use For**: Performance improvements, optimization

### 4. Testing Agent
**Purpose**: Test creation and maintenance  
**Workflow**: Analyze → Generate → Verify  
**Use For**: Test coverage, test generation

---

## Integration with Project Rules

Agents can leverage Project Rules:
- **Architecture patterns**: From `service-architecture.mdc`
- **Security patterns**: From `security-blockchain.mdc`
- **Domain patterns**: From `trading-blockchain-domain.mdc`

**Example**: Architect Agent uses service-architecture rule for design decisions.

---

## Model Context Protocol (MCP) Integration

**Status**: ✅ Available - 12 Working MCPs  
**Location**: `MCPs/Working/` directory  
**Configuration**: `~/.cursor/mcp-hub.json`

### Overview

MCPs (Model Context Protocol servers) provide specialized tools that agents can use to extend their capabilities. All agents should leverage MCPs when appropriate to enhance their workflows.

### Available MCPs

#### Core Services

1. **Filesystem MCP** (`filesystem`)
   - **Purpose**: File operations and directory management
   - **Use When**: Reading/writing files, exploring directory structure
   - **Tools**: 14 tools (read_file, write_file, list_directory, etc.)
   - **Agent Usage**: Use instead of terminal commands for file operations
   - **Example**: Architect Agent uses filesystem MCP to read project structure

2. **Git MCP** (`git`)
   - **Purpose**: Version control operations
   - **Use When**: Committing changes, checking status, managing branches
   - **Tools**: 27 tools (git_status, git_commit, git_branch, etc.)
   - **Agent Usage**: Use for all Git operations instead of terminal
   - **Example**: Security Agent uses git MCP to review commit history

3. **Context7 MCP** (`context7`)
   - **Purpose**: Library documentation search
   - **Use When**: Need documentation for React, FastAPI, web3.py, etc.
   - **Tools**: 2 tools (resolve-library-id, get-library-docs)
   - **Agent Usage**: Research phase - get up-to-date API documentation
   - **Example**: Architect Agent uses Context7 to find FastAPI patterns

4. **StackOverflow MCP** (`stackoverflow`)
   - **Purpose**: Search Stack Overflow for solutions
   - **Use When**: Common coding problems, error solutions
   - **Tools**: 6 tools (search, get_answers, etc.)
   - **Agent Usage**: Troubleshooting and finding solutions
   - **Example**: Testing Agent uses StackOverflow for test patterns

5. **Brave Search MCP** (`brave-search`)
   - **Purpose**: Web search for current information
   - **Use When**: Need latest documentation, best practices, current APIs
   - **Tools**: 2 tools (search, summarize)
   - **Agent Usage**: Research phase - find current best practices
   - **Example**: Performance Agent searches for optimization techniques

6. **CoinGecko MCP** (`coingecko`)
   - **Purpose**: Cryptocurrency price data
   - **Use When**: Need crypto prices, market data
   - **Tools**: Multiple tools for price data
   - **Agent Usage**: Trading-related agents for market data
   - **Example**: Trading Agent uses CoinGecko for price feeds

#### Browser Automation

7. **Puppeteer MCP** (`puppeteer`)
   - **Purpose**: Browser automation and testing
   - **Use When**: E2E testing, web scraping, browser automation
   - **Tools**: 7 tools (navigate, click, screenshot, etc.)
   - **Agent Usage**: Testing Agent for E2E test automation
   - **Example**: Testing Agent uses Puppeteer for browser tests

8. **Cursor Browser Extension MCP** (`cursor-browser-extension`)
   - **Purpose**: Browser interaction via extension
   - **Use When**: Testing frontend, interacting with web apps
   - **Tools**: 18 tools (browser_navigate, browser_click, browser_snapshot, etc.)
   - **Agent Usage**: Frontend testing, UI verification
   - **Example**: Testing Agent uses browser extension for React component testing
   - **Note**: Always call `browser_snapshot` before clicking/typing to get element refs

#### AI & Knowledge

9. **Memory MCP** (`memory`)
   - **Purpose**: Knowledge graph storage and retrieval
   - **Use When**: Store decisions, patterns, relationships
   - **Tools**: 9 tools (create_entities, search_nodes, read_graph, etc.)
   - **Agent Usage**: Store architectural decisions, patterns learned
   - **Example**: Architect Agent stores design decisions in memory MCP

10. **Sequential Thinking MCP** (`sequential-thinking`) ⚠️ **MANDATORY FOR EVERY MESSAGE**
    - **Purpose**: Structured problem-solving through sequential thoughts
    - **Use When**: **EVERY SINGLE USER MESSAGE** - This is mandatory, not optional
    - **Tools**: 1 tool (sequentialthinking)
    - **Agent Usage**: **ALL agents must use this for every interaction**
    - **Workflow**: 
      1. Start every message with sequential thinking to break down the problem
      2. Use sequential thinking to plan the approach
      3. Use sequential thinking to identify required tools/MCPs
      4. Execute the plan
      5. Use sequential thinking to verify the solution
    - **Example**: Every agent interaction starts with sequential thinking MCP

#### Research

11. **ArXiv MCP** (`arxiv`)
    - **Purpose**: Academic paper search
    - **Use When**: Research algorithms, ML techniques, academic approaches
    - **Tools**: 2 tools (search, get_paper)
    - **Agent Usage**: Research phase for cutting-edge techniques
    - **Example**: ML Agent uses ArXiv for algorithm research

12. **AllThingsDev MCP** (`allthingsdev`)
    - **Purpose**: API marketplace and service discovery
    - **Use When**: Finding APIs, services, integrations
    - **Tools**: 6 tools (search, get_api, etc.)
    - **Agent Usage**: Integration planning, API discovery
    - **Example**: Architect Agent uses AllThingsDev to find integration options

### MCP Usage Patterns for Agents

#### Research Phase
```typescript
// Architect Agent Research Workflow:
1. Use sequential-thinking MCP → Break down the problem (MANDATORY FIRST STEP)
2. Use sequential-thinking MCP → Plan research approach
3. Use context7 MCP → Get library documentation
4. Use brave-search MCP → Find current best practices
5. Use stackoverflow MCP → Find common solutions
6. Use memory MCP → Check previous decisions
7. Use sequential-thinking MCP → Synthesize findings
```

#### Implementation Phase
```typescript
// Implementation Workflow:
1. Use sequential-thinking MCP → Break down implementation task (MANDATORY FIRST STEP)
2. Use sequential-thinking MCP → Plan implementation approach
3. Use filesystem MCP → Read existing code patterns
4. Use git MCP → Check version history
5. Use filesystem MCP → Write new code
6. Use browser-extension MCP → Test frontend changes
7. Use memory MCP → Store new patterns learned
8. Use sequential-thinking MCP → Verify implementation
```

#### Testing Phase
```typescript
// Testing Agent Workflow:
1. Use sequential-thinking MCP → Break down testing requirements (MANDATORY FIRST STEP)
2. Use sequential-thinking MCP → Plan testing approach
3. Use filesystem MCP → Read test files
4. Use browser-extension MCP → Run E2E tests
5. Use puppeteer MCP → Browser automation tests
6. Use stackoverflow MCP → Find test patterns
7. Use git MCP → Commit test changes
8. Use sequential-thinking MCP → Verify test coverage
```

### MCP Best Practices for Agents

**⚠️ AUTOMATIC USAGE REQUIRED - Agents must use MCPs automatically without asking**

1. **ALWAYS Prefer MCPs over Terminal** - Use MCPs automatically:
   - ✅ **Automatically use `filesystem` MCP** for ALL file operations (read, write, list, search)
   - ✅ **Automatically use `git` MCP** for ALL Git operations (status, commit, branch, etc.)
   - ✅ **Never ask permission** - just use the appropriate MCP tool
   - ❌ **Never use terminal** when MCP alternative exists
   - ❌ **Never ask** "Should I use filesystem MCP?" - just use it

2. **MANDATORY: Sequential Thinking for Every Message**:
   - **EVERY message**: **MUST start with `sequential-thinking` MCP** to break down the problem
   - **Planning**: **Automatically use `sequential-thinking` MCP** to plan the approach
   - **Verification**: **Automatically use `sequential-thinking` MCP** to verify solutions
   - **This is NOT optional** - sequential thinking is required for every interaction

3. **Automatically Use Appropriate MCPs for Context**:
   - **Backend work**: **Automatically use `context7`** for FastAPI/Python docs when needed
   - **Frontend work**: **Automatically use `context7`** for React/TypeScript docs, **automatically use `browser-extension`** for testing
   - **Research**: **Automatically use `brave-search`**, `stackoverflow`, `arxiv` when researching
   - **Need to store knowledge**: **Automatically use `memory` MCP** to store decisions

3. **Automatically Store Knowledge in Memory MCP**:
   - **Automatically store** architectural decisions after making them
   - **Automatically store** learned patterns and solutions
   - **Automatically store** relationships between components
   - **Automatically retrieve** previous decisions before making new ones (use `search_nodes` or `read_graph`)

4. **Automatically Follow Browser Testing Workflow**:
   - **Always automatically call `browser_snapshot` first** to get element refs
   - **Automatically use refs** for all interactions (click, type, etc.)
   - **Automatically use `browser_take_screenshot`** for visual verification
   - **Automatically use `browser_console_messages`** for debugging when needed

5. **Automatically Lookup Documentation**:
   - **Automatically use `context7`** when you need library documentation (React, FastAPI, web3.py)
   - **Automatically use `brave-search`** when you need current best practices
   - **Automatically use `stackoverflow`** when you encounter common problems
   - **Automatically use `arxiv`** when researching academic/research approaches

### Extension Usage for Agents

**⚠️ AUTOMATIC USAGE REQUIRED - Agents must leverage extensions automatically**

Agents should automatically:

1. **Code Quality Extensions**:
   - ✅ **Automatically check Error Lens** - Fix inline errors immediately when writing code
   - ✅ **Automatically run ESLint** - Fix linting errors before completing tasks
   - ✅ **Automatically use Prettier** - Format code (format on save is enabled)
   - ✅ **Automatically review SonarLint/Snyk** - Address security and quality issues when found
   - ✅ **Never commit code** with errors showing in Error Lens

2. **Testing Extensions**:
   - ✅ **Automatically use Coverage Gutters** - Check test coverage when writing tests
   - ✅ **Automatically use Jest Runner** - Run tests from editor when needed
   - ✅ **Maintain >85% test coverage** - Use Coverage Gutters to verify

3. **Git Extensions**:
   - ✅ **Automatically use GitLens** - Understand code history and blame when investigating code
   - ✅ **Automatically use Git Graph** - Visualize branches when working with Git

4. **Documentation Extensions**:
   - ✅ **Automatically use Markdown All in One** - When editing README or docs
   - ✅ **Automatically use Path Intellisense** - For `@/*` import autocomplete

**Extension Workflow:**
- When writing code → **Automatically check Error Lens** for errors
- Before completing task → **Automatically verify** no ESLint/TypeScript errors
- When writing tests → **Automatically check Coverage Gutters** for coverage
- When investigating code → **Automatically use GitLens** for history

### MCP Integration Examples

#### Architect Agent with MCPs
```markdown
# Architect Agent Workflow

## EVERY MESSAGE STARTS WITH SEQUENTIAL THINKING (MANDATORY)

## RESEARCH Phase
1. Use sequential-thinking MCP → Break down problem (MANDATORY FIRST STEP)
2. Use sequential-thinking MCP → Plan research approach
3. Use memory MCP → Check previous similar decisions
4. Use context7 MCP → Get FastAPI/React documentation
5. Use brave-search MCP → Find current best practices
6. Use filesystem MCP → Explore codebase structure
7. Use sequential-thinking MCP → Synthesize research findings

## PLAN Phase
1. Use sequential-thinking MCP → Design solution (MANDATORY)
2. Use sequential-thinking MCP → Verify design approach
3. Use memory MCP → Store design decisions
4. Use filesystem MCP → Check existing patterns

## BUILD Phase
1. Use sequential-thinking MCP → Plan implementation steps (MANDATORY)
2. Use filesystem MCP → Read existing code
3. Use filesystem MCP → Write new code
4. Use git MCP → Commit changes
5. Use browser-extension MCP → Test frontend
6. Use sequential-thinking MCP → Verify implementation
```

#### Security Agent with MCPs
```markdown
# Security Agent Workflow

1. Use sequential-thinking MCP → Break down security task (MANDATORY FIRST STEP)
2. Use sequential-thinking MCP → Plan security review approach
3. Use filesystem MCP → Read code files
4. Use git MCP → Check commit history for security issues
5. Use memory MCP → Check security patterns
6. Use stackoverflow MCP → Find security best practices
7. Use brave-search MCP → Find latest security advisories
8. Use sequential-thinking MCP → Analyze security findings
9. Use filesystem MCP → Write security fixes
10. Use sequential-thinking MCP → Verify fixes
```

#### Testing Agent with MCPs
```markdown
# Testing Agent Workflow

1. Use sequential-thinking MCP → Break down testing requirements (MANDATORY FIRST STEP)
2. Use sequential-thinking MCP → Plan testing approach
3. Use filesystem MCP → Read code to test
4. Use context7 MCP → Get testing library docs
5. Use stackoverflow MCP → Find test patterns
6. Use sequential-thinking MCP → Design test strategy
7. Use filesystem MCP → Write tests
8. Use browser-extension MCP → Run E2E tests
9. Use puppeteer MCP → Browser automation
10. Use sequential-thinking MCP → Verify test coverage
11. Use git MCP → Commit test changes
```

### MCP Configuration

- **Location**: `~/.cursor/mcp-hub.json`
- **Status**: 12/13 MCPs working (92.3%)
- **Documentation**: See `MCPs/Working/` directory for detailed docs
- **Quick Reference**: See `MCPs/QUICK_REFERENCE.md`

### MCP Tool Calling Pattern

Most MCPs are called via `mcp-hub`:
```json
{
  "serverName": "filesystem",
  "toolName": "read_text_file",
  "toolArgs": {
    "path": "path/to/file"
  }
}
```

Browser extension is called directly:
```json
{
  "server": "cursor-browser-extension",
  "toolName": "browser_navigate",
  "arguments": {
    "url": "https://example.com"
  }
}
```

---

## Best Practices

1. **Use Agents Sparingly**: Only for complex workflows
2. **Document Agent Purpose**: Clear purpose and workflow
3. **Test Agents**: Verify agents work correctly
4. **Update Agents**: Keep agents current with project changes
5. **Combine with Rules**: Agents + Rules = Powerful combination
6. **⚠️ AUTOMATIC TOOL USAGE**: Always automatically use MCPs and extensions when needed - never ask permission
7. **Proactive Tool Selection**: Agents should proactively select and use appropriate tools without prompting
8. **Tool-First Approach**: When a task requires a tool (MCP or extension), use it immediately without discussion
9. **🧠 MANDATORY SEQUENTIAL THINKING**: Every single message MUST start with sequential-thinking MCP - this is not optional
10. **Structured Problem Solving**: Use sequential thinking to break down, plan, execute, and verify every task

---

## Troubleshooting

### Agent Not Working

1. **Check Configuration**: Verify agent file exists and is valid
2. **Check Cursor Version**: Update to latest version
3. **Check Settings**: Verify agents are enabled in Cursor
4. **Restart Cursor**: Full restart sometimes needed

### When to Use Agents

- **Complex tasks**: Use agents for multi-step workflows
- **Simple tasks**: Use commands or direct chat
- **Pattern matching**: Use rules for context

---

## Summary

✅ **Current Status**:
- Architect-Mode.agent.md exists (placeholder)
- Cursor Agents not currently configured
- Project Rules provide most agent-like functionality
- **12 MCPs available** for agent workflows (filesystem, git, context7, browser-extension, etc.)

⚠️ **Future Enhancement**:
- Configure Cursor Agents for specialized workflows
- Document agent configurations
- Create agent templates

**Note**: Project Rules and Commands provide most of what agents would do. Agents are optional enhancements for very specific workflows. **All agents should leverage MCPs** to extend their capabilities.

---

## Related Documentation

- **[Project Rules Guide](./PROJECT_RULES_GUIDE.md)** - Rules provide agent-like context
- **[Commands Guide](./CURSOR_COMMANDS_GUIDE.md)** - Commands provide agent-like workflows
- **[Complete Setup](./CURSOR_SETUP_COMPLETE.md)** - Complete Cursor setup
- **[MCP Documentation](../../MCPs/README.md)** - Complete MCP documentation
- **[MCP Quick Reference](../../MCPs/QUICK_REFERENCE.md)** - Quick lookup for MCP tools
- **[MCP Index](../../MCPs/INDEX.md)** - All available MCPs
