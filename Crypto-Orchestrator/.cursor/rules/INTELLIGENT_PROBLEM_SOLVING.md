# Intelligent Problem-Solving Guide

> **Purpose**: Enable the agent to solve any problem through intelligent, adaptive approaches

## 🤖 Autonomous Problem Solving

**The agent solves problems AUTONOMOUSLY by default:**

- ✅ **Automatically understands** - No asking for clarification unless truly ambiguous
- ✅ **Automatically researches** - Uses intelligence system and MCP tools automatically
- ✅ **Automatically plans** - Creates implementation plan automatically
- ✅ **Automatically implements** - Executes solution without waiting for approval
- ✅ **Automatically validates** - Tests and verifies solution works
- ✅ **Automatically learns** - Stores patterns and decisions for future use

**The agent only asks the user when requirements are genuinely ambiguous or multiple approaches significantly affect user experience.**

## 🎯 Problem-Solving Framework

### Phase 1: Problem Understanding

**Before attempting any solution, the agent MUST:**

1. **Read the problem carefully**
   - What is the user actually trying to achieve?
   - What are the explicit requirements?
   - What are the implicit requirements?
   - What constraints exist?

2. **Gather context**
   - Check knowledge base for similar problems
   - Review extracted patterns for applicable solutions
   - Check decisions log for similar decisions
   - Retrieve relevant patterns from Memory-Bank

3. **Analyze the problem**
   - Classify problem type (bug fix, feature, refactor, etc.)
   - Assess complexity (simple, medium, complex, very complex)
   - Identify dependencies and relationships
   - Determine urgency and priority

### Phase 2: Solution Strategy Selection

**Based on problem understanding, select appropriate strategy:**

#### Strategy 1: Direct Solution (Simple Problems)
- **When**: Clear requirements, well-understood problem, existing patterns
- **Approach**: Apply known pattern directly
- **Time**: Fast (< 5 minutes)

#### Strategy 2: Pattern Matching (Medium Problems)
- **When**: Similar problems solved before, patterns exist
- **Approach**: Find similar pattern, adapt to current problem
- **Time**: Medium (5-15 minutes)

#### Strategy 3: Decomposition (Complex Problems)
- **When**: Problem has multiple parts, complex dependencies
- **Approach**: Break into smaller sub-problems, solve each, combine
- **Time**: Longer (15-60 minutes)

#### Strategy 4: Research-First (Very Complex Problems)
- **When**: Unfamiliar domain, no existing patterns, requires learning
- **Approach**: Research first, then apply learned knowledge
- **Time**: Longest (30+ minutes)

#### Strategy 5: Iterative Refinement (Ambiguous Problems)
- **When**: Requirements unclear, multiple possible solutions
- **Approach**: Start with best guess, refine based on feedback
- **Time**: Variable

### Phase 3: Solution Execution

**Execute solution with monitoring and adaptation:**

1. **Implement solution**
   - Follow selected strategy
   - Apply best practices
   - Write clean, maintainable code

2. **Monitor progress**
   - Check for errors early
   - Verify solution is working
   - Detect issues proactively

3. **Adapt if needed**
   - If current approach isn't working, try alternative
   - Don't persist with failing strategy
   - Learn from failures

4. **Validate solution**
   - Test that solution works
   - Verify it meets requirements
   - Check for edge cases

### Phase 4: Learning and Improvement

**After solving problem:**

1. **Record success**
   - Store solution pattern in knowledge base
   - Save to Memory-Bank for future reference
   - Update extracted patterns if new pattern discovered

2. **Analyze performance**
   - What worked well?
   - What could be improved?
   - What strategies were effective?

3. **Update knowledge**
   - Add new patterns to knowledge base
   - Update heuristics if needed
   - Improve future problem-solving

## 🔄 Error Recovery Workflow

### When an Error Occurs:

1. **Immediate Response** (0-5 seconds)
   - Classify error type
   - Check if retryable
   - Try quick fixes (retry, refresh, clear cache)

2. **Diagnosis** (5-30 seconds)
   - Analyze root cause
   - Check error patterns
   - Review similar errors

3. **Targeted Recovery** (30-60 seconds)
   - Apply specific fix based on diagnosis
   - Try multiple recovery strategies
   - Monitor recovery progress

4. **Alternative Approach** (60+ seconds)
   - If targeted recovery fails, try different approach
   - Use fallback strategies
   - Simplify problem if needed

5. **Learning** (After recovery)
   - Record what worked
   - Record what didn't work
   - Update error patterns

## 🧠 Decision-Making Process

### For Every Decision:

1. **Gather Information**
   - What do I know?
   - What do I need to know?
   - What are the constraints?

2. **Evaluate Options**
   - What are the possible approaches?
   - What are the pros and cons of each?
   - What are the risks?

3. **Consider Context**
   - What worked in similar situations?
   - What are the current system conditions?
   - What are the user's preferences?

4. **Make Decision**
   - Select best option based on evaluation
   - Consider trade-offs
   - Be ready to adapt

5. **Execute and Monitor**
   - Implement decision
   - Monitor results
   - Adjust if needed

## 🎯 Problem-Solving Patterns

### Pattern 1: Search-First Approach

**When**: Need to find existing solution or pattern

1. Search codebase for similar implementations
2. Check knowledge base for patterns
3. Review extracted patterns
4. Check Memory-Bank for stored solutions
5. If found, adapt to current problem
6. If not found, proceed to implementation

### Pattern 2: Incremental Implementation

**When**: Complex problem or uncertain requirements

1. Start with minimal working solution
2. Test and validate
3. Add features incrementally
4. Test after each addition
5. Refine based on feedback

### Pattern 3: Test-Driven Approach

**When**: Fixing bugs or adding features with clear requirements

1. Write test for expected behavior
2. Run test (should fail)
3. Implement solution
4. Run test (should pass)
5. Refactor if needed

### Pattern 4: Research-Then-Implement

**When**: Unfamiliar domain or technology

1. Research best practices
2. Find examples and patterns
3. Understand the approach
4. Implement based on research
5. Validate and refine

### Pattern 5: Decompose-and-Conquer

**When**: Large or complex problem

1. Break into smaller sub-problems
2. Solve each sub-problem
3. Combine solutions
4. Test integration
5. Refine as needed

## 🚨 Critical Rules for Problem-Solving

1. **Never give up without trying multiple approaches**
   - Try at least 3 different strategies before asking for help
   - Use fallback strategies
   - Simplify problem if needed

2. **Always learn from experience**
   - Record successful patterns
   - Record failed attempts
   - Update knowledge base

3. **Proactively detect issues**
   - Monitor for warning signs
   - Take preventive action
   - Don't wait for errors

4. **Adapt strategies based on results**
   - If strategy isn't working, try different one
   - Don't persist with failing approach
   - Learn what works and what doesn't

5. **Use context intelligently**
   - Gather all relevant information
   - Consider similar past situations
   - Make informed decisions

6. **Validate solutions thoroughly**
   - Test that solution works
   - Check edge cases
   - Verify requirements met

7. **Document decisions and rationale**
   - Explain why approach was chosen
   - Document trade-offs
   - Store in Memory-Bank

---

**Remember**: Intelligent problem-solving means:
- ✅ Understanding before acting
- ✅ Trying multiple approaches
- ✅ Learning from experience
- ✅ Adapting to circumstances
- ✅ Never giving up easily
