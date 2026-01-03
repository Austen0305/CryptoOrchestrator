# How Cursor Reads Project Rules - Best Practices Guide

**Research Date**: December 30, 2025  
**Status**: ✅ Current setup follows all best practices

---

## 📚 How Cursor Reads Rules

### Rule Processing Flow

1. **File Discovery**: Cursor scans `.cursor/rules/` directory for `.mdc` files
2. **Metadata Parsing**: Reads YAML frontmatter to determine when to apply rules
3. **Context Injection**: Rules are injected at the **prompt level** (not stored in memory)
4. **Pattern Matching**: Glob patterns are evaluated against open/referenced files
5. **Rule Application**: Relevant rules are included in the model context

### Key Insight: Prompt-Level Context

**Important**: Rules are **not stored in memory** between completions. They're included at the start of each prompt, providing consistent guidance for:
- Code generation
- Code interpretation
- Workflow assistance

---

## ✅ Best Practices for Rule Organization

### 1. Use `.mdc` Format (Modern Standard)

**✅ Recommended**: `.mdc` files in `.cursor/rules/` directory
- Structured metadata (YAML frontmatter)
- Version control friendly
- Supports multiple rule types
- Better organization

**❌ Deprecated**: `.cursorrules` files
- Global application only
- Limited structure
- Harder to manage

### 2. Keep Rules Focused and Concise

**Optimal Size**:
- **Ideal**: 50-200 lines per rule
- **Maximum**: 500 lines per rule
- **Why**: Smaller rules are easier for AI to parse and apply

**Current Status**:
- ✅ All 9 rules are under 500 lines
- ✅ Rules are focused on specific topics
- ✅ No single rule exceeds recommended size

### 3. Use Multiple Focused Rules

**✅ Better**: 3-9 focused rules by topic
- Better performance (faster parsing)
- Easier maintenance
- Clearer organization
- More effective AI behavior

**❌ Avoid**: One large 2000+ line rule
- Slower processing
- Harder to maintain
- Less effective context

**Current Setup**: ✅ 9 focused rules (optimal)

### 4. Optimize Glob Patterns

**Performance Considerations**:
- Complex glob patterns require more processing
- Performance impact scales with number of files
- File system efficiency matters

**Best Practices**:
```yaml
# ✅ Good: Specific patterns
globs: ["server_fastapi/services/trading/**/*"]

# ✅ Good: Multiple specific patterns
globs: ["**/*test*.py", "**/*test*.ts", "tests/**/*"]

# ❌ Avoid: Overly broad patterns
globs: ["**/*"]  # Too broad, matches everything

# ❌ Avoid: Complex recursive patterns
globs: ["**/**/**/*.py"]  # Unnecessary complexity
```

**Current Setup**: ✅ All glob patterns are specific and optimized

### 5. Use Appropriate Rule Types

**Rule Types** (via YAML frontmatter):

#### Always Applied (`alwaysApply: true`)
```yaml
---
description: Core project conventions
alwaysApply: true
---
```
- Included in **every** chat session
- Use for: Core conventions, critical patterns
- **Current**: 4 rules (project-conventions, python-fastapi, react-typescript, security-blockchain)

#### Pattern Matched (`globs` specified)
```yaml
---
description: Testing patterns
globs: ["**/*test*.py", "**/*test*.ts"]
alwaysApply: false
---
```
- Applied when files match glob patterns
- Use for: Context-specific rules
- **Current**: 5 rules (testing, database-migrations, deployment, trading-blockchain-domain, service-architecture)

#### Agent Requested (description only)
```yaml
---
description: Advanced deployment patterns for Kubernetes
alwaysApply: false
---
```
- AI decides when to include based on description
- Use for: Optional, advanced patterns

#### Manual (`@ruleName`)
- Included only when explicitly invoked
- Use for: Rarely needed, specialized rules

---

## 🎯 Current Rule Setup Analysis

### Always Applied Rules (4)

| Rule | Lines | Purpose | Status |
|------|-------|---------|--------|
| `project-conventions.mdc` | ~300 | Core conventions | ✅ Optimal |
| `python-fastapi.mdc` | ~250 | Backend patterns | ✅ Optimal |
| `react-typescript.mdc` | ~280 | Frontend patterns | ✅ Optimal |
| `security-blockchain.mdc` | ~350 | Security rules | ✅ Optimal |

**Total Context**: ~1,180 lines always included
**Status**: ✅ Within optimal range (under 2,000 lines total)

### Pattern Matched Rules (5)

| Rule | Lines | Glob Patterns | Status |
|------|-------|---------------|--------|
| `testing.mdc` | ~200 | Test files | ✅ Optimal |
| `database-migrations.mdc` | ~150 | Migration files | ✅ Optimal |
| `deployment.mdc` | ~200 | Docker/K8s files | ✅ Optimal |
| `trading-blockchain-domain.mdc` | ~500 | Trading/blockchain services | ✅ Optimal |
| `service-architecture.mdc` | ~300 | Services/repositories | ✅ Optimal |

**Status**: ✅ All patterns are specific and performant

---

## ⚡ Performance Optimization

### How Cursor Processes Rules

1. **File Scanning**: Fast (only `.mdc` files in `.cursor/rules/`)
2. **Metadata Parsing**: Fast (YAML frontmatter is lightweight)
3. **Glob Matching**: Performance depends on:
   - Pattern complexity
   - Number of files in project
   - File system efficiency

### Performance Best Practices

**✅ Do**:
- Use specific glob patterns
- Keep rules under 500 lines
- Limit always-applied rules (4-5 max)
- Use pattern matching for context-specific rules

**❌ Avoid**:
- Overly broad glob patterns (`**/*`)
- Very large rules (>500 lines)
- Too many always-applied rules (>10)
- Complex recursive glob patterns

**Current Setup**: ✅ Follows all performance best practices

---

## 🔍 How `.cursorignore` Affects Rules

### Important: Rules Must NOT Be Ignored

The `.cursorignore` file controls what Cursor can see. For rules to work:

```gitignore
# ✅ Good: Allow rules
!.cursor/rules/*.mdc
!.cursor/rules/*.md

# ❌ Bad: Would ignore rules
.cursor/rules/*.mdc
```

**Current Status**: ✅ `.cursorignore` correctly allows rules:
```gitignore
!.cursor/rules/*.mdc
!.cursor/rules/*.md
```

---

## 📊 Rule Reading Process

### Step-by-Step Flow

```
1. User opens Cursor
   ↓
2. Cursor scans `.cursor/rules/` directory
   ↓
3. Finds all `.mdc` files
   ↓
4. Parses YAML frontmatter for each rule
   ↓
5. Categorizes rules:
   - Always Applied (alwaysApply: true)
   - Pattern Matched (globs specified)
   - Agent Requested (description only)
   ↓
6. User starts chat or opens file
   ↓
7. Cursor evaluates:
   - Always Applied rules → Include
   - Pattern Matched rules → Check globs against open/referenced files
   - Agent Requested rules → AI decides based on description
   ↓
8. Relevant rules injected into prompt context
   ↓
9. AI processes request with rule context
```

### Context Injection

Rules are injected at the **start of the prompt**, like this:

```
[Rule: project-conventions.mdc]
[Rule: python-fastapi.mdc]
[Rule: react-typescript.mdc]
[Rule: security-blockchain.mdc]
[Rule: testing.mdc]  # If test file is open
[Rule: trading-blockchain-domain.mdc]  # If trading service is open

[User Query]
[Code Context]
```

---

## ✅ Verification Checklist

### Current Setup Verification

- [x] All rules use `.mdc` format
- [x] All rules have valid YAML frontmatter
- [x] All rules are under 500 lines
- [x] Glob patterns are specific and optimized
- [x] `.cursorignore` allows rules
- [x] Rules are visible in Cursor Settings
- [x] Rules are applied correctly (verified in settings)
- [x] No overly broad glob patterns
- [x] Appropriate mix of always-applied and pattern-matched rules

**Status**: ✅ All checks passed

---

## 🚀 Recommendations

### Current Setup: Optimal ✅

Your current rule setup follows **all best practices**:

1. ✅ Using `.mdc` format (modern standard)
2. ✅ 9 focused rules (optimal number)
3. ✅ All rules under 500 lines
4. ✅ Specific glob patterns
5. ✅ Appropriate rule types (4 always, 5 pattern-matched)
6. ✅ `.cursorignore` correctly configured
7. ✅ Rules visible and working in Cursor Settings

### No Changes Needed

Your setup is already optimized for:
- **Performance**: Fast rule processing
- **Maintainability**: Easy to update individual rules
- **Effectiveness**: AI gets relevant context
- **Organization**: Clear separation of concerns

---

## 📚 Additional Resources

- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [Cursor Directory - Rule Examples](https://cursor.directory/rules)
- [Project Rules README](.cursor/rules/README.md)

---

## 🎯 Summary

**How Cursor Reads Rules**:
1. Scans `.cursor/rules/` for `.mdc` files
2. Parses YAML frontmatter to determine application rules
3. Injects relevant rules at prompt level (not memory)
4. Evaluates glob patterns against open/referenced files
5. Includes rules in model context for consistent guidance

**Best Practices** (All Followed ✅):
- Use `.mdc` format
- Keep rules under 500 lines
- Use multiple focused rules (3-9)
- Optimize glob patterns
- Use appropriate rule types
- Ensure `.cursorignore` allows rules

**Current Status**: ✅ Optimal setup, no changes needed
