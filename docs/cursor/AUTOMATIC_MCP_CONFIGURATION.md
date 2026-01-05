# Automatic MCP, Tools & Extensions Configuration Guide

**Date**: January 4, 2026  
**Status**: ✅ Current Best Practices  
**Last Updated**: 2026-01-04

---

## Overview

This guide explains how to configure Cursor Agent to automatically use MCPs (Model Context Protocol), tools, and extensions without requiring manual approval for each action. This enables seamless, efficient workflows where agents can proactively use available tools.

---

## Table of Contents

1. [Cursor IDE Settings Configuration](#cursor-ide-settings-configuration)
2. [MCP Server Configuration](#mcp-server-configuration)
3. [Project Rules Integration](#project-rules-integration)
4. [Auto-Run Mode Options](#auto-run-mode-options)
5. [Security Considerations](#security-considerations)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Cursor IDE Settings Configuration

### Step 1: Access Agent Settings

1. Open **Cursor IDE**
2. Navigate to **Settings** (or press `Ctrl+,` / `Cmd+,`)
3. Go to **Agent** section (or **Cursor > Settings > Agent**)

### Step 2: Configure Auto-Run Mode

In the **Agent** section, locate **"Auto-Run Mode"** and select one of the following:

#### Option 1: Ask Every Time (Most Secure - Default)
- **Behavior**: Cursor prompts for confirmation before executing any MCP tool
- **Use Case**: Debugging, working with sensitive data, untrusted MCPs
- **Security**: Highest - full control over every action
- **Workflow Impact**: Requires manual approval for each tool call

#### Option 2: Use Allowlist (Balanced - Recommended)
- **Behavior**: Cursor automatically runs commands pre-approved in your allowlist; prompts for new/unlisted commands
- **Use Case**: General development workflows, trusted MCPs
- **Security**: Medium - balance between automation and control
- **Workflow Impact**: Seamless for approved tools, approval needed for new ones

#### Option 3: Run Everything (Maximum Automation)
- **Behavior**: Cursor executes all MCP tool calls without asking for confirmation
- **Use Case**: Rapid testing, prototyping, sandbox/development environments
- **Security**: Lower - relies on trust in configured MCPs
- **Workflow Impact**: Fully automated, no interruptions

**⚠️ Security Warning**: "Run Everything" mode increases risk of executing unintended commands. Only use with trusted MCP servers in safe environments.

### Step 3: Configure MCP Servers

1. Navigate to **Settings > Tools & Integrations > MCP** (or **Cursor > Settings > Features > MCP Servers**)
2. Click **"+ Add New MCP Server"**
3. Configure each server:

#### Command Mode (Recommended)
- **Name**: Descriptive name (e.g., "Filesystem", "Git", "Context7")
- **Type**: Select **"Command"** or **"stdio"**
- **Command**: Enter the command to run the server
  - Example: `npx -y @modelcontextprotocol/server-filesystem`
  - Or if installed globally: `cursor-azure-devops-mcp`
- **Environment Variables**: Add any required env vars (API keys, paths, etc.)

#### SSE Mode (Alternative)
- **Name**: Descriptive name
- **Type**: Select **"sse"**
- **URL**: Enter the SSE endpoint URL (e.g., `http://localhost:3000/sse`)
- **Note**: SSE mode may be more prone to connection issues

### Step 4: Authenticate MCP Servers (if required)

Some MCP servers require authentication:
1. In MCP settings, locate servers with **"Needs authentication"** status
2. Click on the authentication status
3. Follow the prompts to log in and authorize Cursor

---

## MCP Server Configuration

### Configuration File Location

MCP servers can be configured in two ways:

#### 1. Global Configuration
- **Location**: `~/.cursor/mcp.json` (or `C:\Users\<YourName>\.cursor\mcp.json` on Windows)
- **Scope**: Applies to all Cursor projects
- **Format**: JSON configuration file

#### 2. Project-Specific Configuration
- **Location**: `<project-root>/mcp.json`
- **Scope**: Applies only to the current project
- **Format**: JSON configuration file

### Example MCP Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_DIRECTORIES": "/path/to/allowed"
      }
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "env": {
        "REPO_PATH": "."
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### MCP Hub Configuration (Alternative)

If using `mcp-hub` for centralized MCP management:

- **Location**: `~/.cursor/mcp-hub.json`
- **Purpose**: Manages multiple MCP servers through a hub
- **Current Project**: Uses `mcp-hub.json` with 12 working MCPs

---

## Project Rules Integration

### How Project Rules Enable Automatic Usage

While Cursor IDE settings control **whether** tools can run automatically, **project rules** control **how** agents should use tools. Your project already has comprehensive rules:

#### Key Rule Files

1. **`.cursor/rules/project-conventions.mdc`**
   - Defines automatic MCP usage patterns
   - Mandates sequential thinking for every message
   - Specifies which MCPs to use for which tasks

2. **`.cursor/rules/react-typescript.mdc`**
   - Frontend-specific MCP usage (browser-extension, context7)
   - Extension usage patterns (Error Lens, ESLint, Prettier)

3. **`.cursor/rules/python-fastapi.mdc`**
   - Backend-specific MCP usage (filesystem, git, context7)
   - Python tooling patterns

4. **`docs/cursor/AGENTS.md`**
   - Comprehensive MCP integration guide
   - Agent workflow patterns
   - MCP usage examples

### Rule-Based Automatic Usage

Your project rules instruct agents to:

✅ **Automatically use MCPs** without asking permission:
- `filesystem` MCP for all file operations
- `git` MCP for all Git operations
- `context7` MCP for documentation lookup
- `browser-extension` MCP for frontend testing
- `sequential-thinking` MCP for every message (mandatory)

✅ **Automatically use extensions**:
- Error Lens for inline error checking
- ESLint/TypeScript for code quality
- Prettier for formatting
- Coverage Gutters for test coverage

### How Rules + Settings Work Together

```
┌─────────────────────────────────────────────────────────┐
│  Cursor IDE Settings (Auto-Run Mode)                     │
│  └─ Controls: "Can tools run automatically?"            │
│     • Ask Every Time                                      │
│     • Use Allowlist                                       │
│     • Run Everything                                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Project Rules (.cursor/rules/*.mdc)                     │
│  └─ Controls: "How should agents use tools?"            │
│     • Which MCPs to use for which tasks                  │
│     • When to use extensions                             │
│     • Workflow patterns                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Agent Behavior                                          │
│  └─ Result: Automatic, intelligent tool usage            │
│     • Uses MCPs proactively                              │
│     • Follows project patterns                           │
│     • No permission prompts (if auto-run enabled)        │
└─────────────────────────────────────────────────────────┘
```

---

## Auto-Run Mode Options

### Detailed Comparison

| Mode | Approval Required | Security Level | Workflow Speed | Best For |
|------|------------------|----------------|----------------|----------|
| **Ask Every Time** | Always | ⭐⭐⭐⭐⭐ Highest | ⭐ Slowest | Production, sensitive data |
| **Use Allowlist** | Only for new tools | ⭐⭐⭐ Medium | ⭐⭐⭐ Fast | General development |
| **Run Everything** | Never | ⭐⭐ Lower | ⭐⭐⭐⭐⭐ Fastest | Testing, sandbox environments |

### Recommended Configuration

**For Development:**
- **Auto-Run Mode**: "Use Allowlist"
- **Allowlist**: Add trusted MCPs (filesystem, git, context7, browser-extension)
- **Result**: Seamless workflow for common operations, approval for new tools

**For Production:**
- **Auto-Run Mode**: "Ask Every Time" or "Use Allowlist"
- **Allowlist**: Only production-safe MCPs
- **Result**: Security with controlled automation

**For Testing/Prototyping:**
- **Auto-Run Mode**: "Run Everything"
- **Environment**: Sandbox/development only
- **Result**: Maximum automation for rapid iteration

---

## Security Considerations

### ⚠️ Important Security Notes

1. **Auto-Run Risks**:
   - Enabling auto-run allows MCPs to execute commands without approval
   - Malicious or misconfigured MCPs could cause harm
   - Always verify MCP server sources and configurations

2. **Past Vulnerabilities**:
   - A previous vulnerability allowed attackers to modify approved MCP configurations
   - This has been addressed in recent Cursor updates
   - **Always keep Cursor updated** to latest version

3. **Best Practices**:
   - ✅ Only use trusted MCP servers from verified sources
   - ✅ Review MCP configurations before enabling auto-run
   - ✅ Use "Use Allowlist" mode for balance of security and automation
   - ✅ Regularly audit configured MCP servers
   - ✅ Keep Cursor and MCP servers updated
   - ✅ Use "Ask Every Time" for sensitive operations

4. **MCP Server Trust**:
   - Verify MCP server sources (GitHub, npm, official repositories)
   - Review MCP server code if possible
   - Check MCP server permissions and capabilities
   - Start with "Ask Every Time" for new MCPs, then add to allowlist once trusted

### Security Checklist

Before enabling auto-run:
- [ ] Verified MCP server source and authenticity
- [ ] Reviewed MCP server capabilities and permissions
- [ ] Tested MCP server in "Ask Every Time" mode first
- [ ] Updated Cursor to latest version
- [ ] Configured appropriate auto-run mode for environment
- [ ] Set up allowlist with only trusted MCPs (if using allowlist mode)

---

## Best Practices

### 1. Start Conservative, Then Expand

1. **Initial Setup**: Use "Ask Every Time" mode
2. **Test MCPs**: Verify each MCP works correctly
3. **Build Allowlist**: Add trusted MCPs to allowlist one by one
4. **Monitor**: Watch for unexpected behavior
5. **Expand**: Gradually add more MCPs to allowlist

### 2. Use Project Rules for Behavior

- Configure **what** tools to use via project rules (`.cursor/rules/`)
- Configure **whether** tools can run automatically via Cursor settings
- Rules provide context-aware tool selection
- Settings provide security controls

### 3. Environment-Specific Configuration

- **Development**: "Use Allowlist" or "Run Everything"
- **Staging**: "Use Allowlist" with production-safe MCPs
- **Production**: "Ask Every Time" or strict allowlist

### 4. MCP Organization

- Group related MCPs (e.g., all file operations, all Git operations)
- Document MCP purposes and use cases
- Maintain a list of configured MCPs and their purposes
- Review and clean up unused MCPs periodically

### 5. Extension Integration

- Extensions work independently of MCP auto-run settings
- Configure extensions in VS Code/Cursor settings
- Use project rules to guide extension usage patterns
- Enable format on save, lint on save, etc.

---

## Troubleshooting

### MCP Not Running Automatically

**Problem**: MCP tools still require approval even with auto-run enabled

**Solutions**:
1. ✅ Verify auto-run mode is set correctly in Settings > Agent
2. ✅ Check MCP server is properly configured in Settings > MCP
3. ✅ Ensure MCP server is in allowlist (if using allowlist mode)
4. ✅ Restart Cursor after changing settings
5. ✅ Check MCP server is running and accessible
6. ✅ Verify MCP server authentication (if required)

### MCP Server Not Found

**Problem**: Cursor can't find or connect to MCP server

**Solutions**:
1. ✅ Verify MCP server command is correct
2. ✅ Check MCP server is installed (if using npx, it will auto-install)
3. ✅ Verify environment variables are set correctly
4. ✅ Check MCP server logs for errors
5. ✅ Test MCP server command manually in terminal

### Auto-Run Not Working

**Problem**: Tools still prompt for approval

**Solutions**:
1. ✅ Verify you're using the correct auto-run mode
2. ✅ Check if MCP is in allowlist (allowlist mode)
3. ✅ Restart Cursor completely (not just reload window)
4. ✅ Check Cursor version (update if needed)
5. ✅ Verify MCP server configuration is valid JSON

### Extension Not Working

**Problem**: Extensions not providing expected functionality

**Solutions**:
1. ✅ Verify extension is installed and enabled
2. ✅ Check extension settings in VS Code/Cursor settings
3. ✅ Review extension documentation
4. ✅ Check for extension conflicts
5. ✅ Update extension to latest version

---

## Current Project Configuration

### Your Current Setup

**MCP Configuration**: `~/.cursor/mcp-hub.json`  
**Working MCPs**: 12/13 (92.3%)  
**Status**: ✅ Operational

**Configured MCPs**:
- ✅ filesystem (14 tools)
- ✅ git (27 tools)
- ✅ context7 (2 tools)
- ✅ stackoverflow (6 tools)
- ✅ brave-search (2 tools)
- ✅ coingecko (multiple tools)
- ✅ puppeteer (7 tools)
- ✅ cursor-browser-extension (18 tools)
- ✅ memory (9 tools)
- ✅ sequential-thinking (1 tool)
- ✅ arxiv (2 tools)
- ✅ allthingsdev (6 tools)

**Project Rules**: Comprehensive rules in `.cursor/rules/` that instruct automatic MCP usage

**Next Steps**:
1. Configure auto-run mode in Cursor Settings > Agent
2. Add trusted MCPs to allowlist (if using allowlist mode)
3. Test automatic tool usage
4. Monitor and adjust as needed

---

## Summary

### Quick Setup Checklist

- [ ] Open Cursor Settings > Agent
- [ ] Select appropriate Auto-Run Mode:
  - [ ] "Ask Every Time" (most secure)
  - [ ] "Use Allowlist" (recommended for development)
  - [ ] "Run Everything" (testing/sandbox only)
- [ ] Configure MCP servers in Settings > Tools & Integrations > MCP
- [ ] Add trusted MCPs to allowlist (if using allowlist mode)
- [ ] Verify project rules are in place (`.cursor/rules/`)
- [ ] Test automatic tool usage
- [ ] Monitor and adjust configuration as needed

### Key Takeaways

1. **Cursor Settings** control **whether** tools can run automatically
2. **Project Rules** control **how** agents should use tools
3. **"Use Allowlist"** mode provides best balance of security and automation
4. **Project rules** already instruct agents to use MCPs automatically
5. **Security** should be prioritized - start conservative, expand gradually

---

## Related Documentation

- **[Agents Guide](./AGENTS.md)** - Comprehensive agent and MCP documentation
- **[MCP Index](../../MCPs/INDEX.md)** - All available MCPs
- **[MCP Quick Reference](../../MCPs/QUICK_REFERENCE.md)** - Quick lookup for MCP tools
- **[Project Rules](../.cursor/rules/)** - Project-specific rules and patterns
- **[Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol)** - Official Cursor MCP docs

---

**Last Updated**: January 4, 2026  
**Maintained By**: CryptoOrchestrator Development Team
