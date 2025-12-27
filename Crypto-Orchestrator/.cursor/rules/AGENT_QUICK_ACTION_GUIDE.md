# Agent Quick Action Guide

> **Purpose**: Immediate action steps for the agent when encountering problems

## 🤖 Autonomous Quick Actions

**The agent AUTOMATICALLY takes quick actions without asking:**

- ✅ **Automatically assesses** - Classifies errors immediately
- ✅ **Automatically recovers** - Tries recovery strategies automatically
- ✅ **Automatically fixes** - Applies fixes without asking
- ✅ **Automatically verifies** - Tests fixes automatically
- ✅ **Automatically learns** - Stores solutions for future use

**The agent does NOT ask** - it automatically takes quick actions for all problems.

## 🚨 When You Encounter an Error (AUTOMATIC)

**The agent AUTOMATICALLY handles errors without asking - NO ASKING REQUIRED.**

### Step 1: AUTOMATIC Immediate Assessment (0-5 seconds)

**The agent AUTOMATICALLY assesses errors:**

```typescript
// AUTOMATICALLY: Quick error classification
if (error.message.includes('connection') || error.message.includes('timeout')) {
  // AUTOMATICALLY: Connection error - try retry
  await retryWithBackoff(operation);
} else if (error.message.includes('auth') || error.message.includes('401')) {
  // AUTOMATICALLY: Auth error - refresh token
  await refreshAuthToken();
} else if (error.message.includes('validation') || error.message.includes('422')) {
  // AUTOMATICALLY: Validation error - fix input
  await fixInputData();
} else {
  // AUTOMATICALLY: Unknown error - proceed to diagnosis
  await diagnoseError(error);
}
```

**The agent does NOT ask** - it automatically assesses and classifies errors.

### Step 2: AUTOMATIC Quick Recovery Attempts (5-30 seconds)

**The agent AUTOMATICALLY tries recovery strategies:**

1. ✅ **AUTOMATICALLY** Retry with backoff (if retryable)
2. ✅ **AUTOMATICALLY** Clear cache (if cache-related)
3. ✅ **AUTOMATICALLY** Refresh connection (if connection-related)
4. ✅ **AUTOMATICALLY** Reset state (if state-related)

**The agent does NOT ask** - it automatically tries recovery strategies.

### Step 3: AUTOMATIC Pattern Matching (30-60 seconds)

**The agent AUTOMATICALLY matches patterns:**

1. ✅ **AUTOMATICALLY** Search knowledge base for similar errors
2. ✅ **AUTOMATICALLY** Check extracted patterns for solutions
3. ✅ **AUTOMATICALLY** Review Memory-Bank for stored solutions
4. ✅ **AUTOMATICALLY** Check decisions log for similar situations

**The agent does NOT ask** - it automatically matches patterns.

### Step 4: AUTOMATIC Targeted Fix (60+ seconds)

**The agent AUTOMATICALLY applies fixes:**

1. ✅ **AUTOMATICALLY** Apply specific fix based on pattern match
2. ✅ **AUTOMATICALLY** Try alternative approach if first fix fails
3. ✅ **AUTOMATICALLY** Use fallback strategy if alternatives fail

**The agent does NOT ask** - it automatically fixes errors.

## 🎯 When You Need to Solve a Problem (AUTOMATIC)

**The agent AUTOMATICALLY solves problems without asking - NO ASKING REQUIRED.**

### AUTOMATIC Quick Decision Tree

**The agent AUTOMATICALLY follows this decision tree:**

```
AUTOMATICALLY: Is this a known problem?
├─ Yes → AUTOMATICALLY Use stored solution from knowledge base
└─ No → AUTOMATICALLY Continue

AUTOMATICALLY: Is there a similar problem?
├─ Yes → AUTOMATICALLY Adapt similar solution
└─ No → AUTOMATICALLY Continue

AUTOMATICALLY: Is the problem simple?
├─ Yes → AUTOMATICALLY Direct solution approach
└─ No → AUTOMATICALLY Continue

AUTOMATICALLY: Is the problem complex?
├─ Yes → AUTOMATICALLY Decompose into sub-problems
└─ No → AUTOMATICALLY Research-first approach
```

### AUTOMATIC Action Checklist

**The agent AUTOMATICALLY performs all actions:**

- ✅ **AUTOMATICALLY** Understand the problem - What is the user trying to achieve?
- ✅ **AUTOMATICALLY** Check knowledge base - Is there an existing solution?
- ✅ **AUTOMATICALLY** Search codebase - How is this handled elsewhere?
- ✅ **AUTOMATICALLY** Check patterns - What patterns apply?
- ✅ **AUTOMATICALLY** Select strategy - Which approach is best?
- ✅ **AUTOMATICALLY** Implement solution - Execute with monitoring
- ✅ **AUTOMATICALLY** Validate solution - Does it work?
- ✅ **AUTOMATICALLY** Learn from experience - Store for future

**The agent does NOT ask** - it automatically performs all actions.

## 🔄 When You Need to Make a Decision

### Decision Framework

1. **Gather Information**
   - What do I know?
   - What do I need to know?
   - What are the constraints?

2. **Evaluate Options**
   - List possible approaches
   - Pros and cons of each
   - Risks and benefits

3. **Consider Context**
   - Similar past decisions
   - Current system state
   - User preferences

4. **Make Decision**
   - Select best option
   - Document rationale
   - Execute with monitoring

## 🛠️ Common Problem Types and Solutions

### Connection Issues
1. Retry with exponential backoff
2. Check health of service
3. Restart connection pool
4. Use fallback service

### Authentication Issues
1. Refresh token
2. Re-authenticate
3. Use fallback auth method
4. Check token expiration

### Validation Issues
1. Fix input data
2. Use default values
3. Skip validation (if safe)
4. Request user input

### Performance Issues
1. Clear cache
2. Optimize query
3. Use pagination
4. Defer non-critical operations

### Unknown Errors
1. Classify error type
2. Search for similar errors
3. Try generic recovery strategies
4. Escalate if all fail

## 📋 AUTOMATIC Pre-Action Checklist

**The agent AUTOMATICALLY performs all pre-action checks - NO ASKING:**

Before starting any task, AUTOMATICALLY:

- ✅ **AUTOMATICALLY** Check system health
- ✅ **AUTOMATICALLY** Review knowledge base
- ✅ **AUTOMATICALLY** Check for similar problems
- ✅ **AUTOMATICALLY** Assess problem complexity
- ✅ **AUTOMATICALLY** Select appropriate strategy
- ✅ **AUTOMATICALLY** Prepare fallback plans

**The agent does NOT ask** - it automatically performs all pre-action checks.

## 🎓 AUTOMATIC Learning Checklist

**The agent AUTOMATICALLY learns from every task - NO ASKING:**

After completing any task, AUTOMATICALLY:

- ✅ **AUTOMATICALLY** Record successful patterns
- ✅ **AUTOMATICALLY** Document failed attempts
- ✅ **AUTOMATICALLY** Update knowledge base
- ✅ **AUTOMATICALLY** Store in Memory-Bank
- ✅ **AUTOMATICALLY** Update heuristics if needed

**The agent does NOT ask** - it automatically learns from every experience.

## 🚀 Quick Reference Commands

### When You Need Information
- `codebase_search` - Search codebase for patterns
- `read_file` - Read relevant files
- `grep` - Find specific code patterns
- Memory-Bank MCP - Retrieve stored patterns

### When You Need to Fix Something
- Check `.cursor/rules/INTELLIGENT_PROBLEM_SOLVING.md` for framework
- Check `.cursor/rules/AGENT_INTELLIGENCE_ENHANCEMENT.md` for recovery strategies
- Check `.cursor/rules/MCP_TROUBLESHOOTING_QUICK_REFERENCE.md` for MCP issues

### When You Need to Make a Decision
- Check `.cursor/decisions.md` for similar decisions
- Check Memory-Bank for stored decisions
- Use decision framework from problem-solving guide

---

**Remember**: 
- ✅ Try multiple approaches before giving up
- ✅ Learn from every experience
- ✅ Use context intelligently
- ✅ Adapt strategies based on results
- ✅ Never stop learning
