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

## Best Practices

1. **Use Agents Sparingly**: Only for complex workflows
2. **Document Agent Purpose**: Clear purpose and workflow
3. **Test Agents**: Verify agents work correctly
4. **Update Agents**: Keep agents current with project changes
5. **Combine with Rules**: Agents + Rules = Powerful combination

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

⚠️ **Future Enhancement**:
- Configure Cursor Agents for specialized workflows
- Document agent configurations
- Create agent templates

**Note**: Project Rules and Commands provide most of what agents would do. Agents are optional enhancements for very specific workflows.

---

## Related Documentation

- **[Project Rules Guide](./PROJECT_RULES_GUIDE.md)** - Rules provide agent-like context
- **[Commands Guide](./CURSOR_COMMANDS_GUIDE.md)** - Commands provide agent-like workflows
- **[Complete Setup](./CURSOR_SETUP_COMPLETE.md)** - Complete Cursor setup
