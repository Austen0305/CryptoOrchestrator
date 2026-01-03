# User Rules Verification Guide

Quick tests to verify your User Rules are working correctly.

---

## ✅ Quick Verification Tests

### Test 1: Communication & Core Quality

**Ask Cursor:**
```
Create a simple Python function that calculates the sum of two numbers
```

**Expected (Rule 1 working):**
- ✅ Function has type hints
- ✅ Includes docstring
- ✅ Clean, readable code
- ✅ Proper error handling if applicable

**If it doesn't:**
- ❌ No type hints
- ❌ No docstring
- ❌ Messy code

---

### Test 2: TypeScript & Frontend (Rule 2)

**Ask Cursor:**
```
Create a React button component that accepts onClick and label props
```

**Expected (Rule 2 working):**
- ✅ Functional component (not class)
- ✅ TypeScript interface for props
- ✅ No `any` types
- ✅ Proper prop typing
- ✅ Uses TypeScript strict mode patterns

**If it doesn't:**
- ❌ Uses `any` type
- ❌ No TypeScript types
- ❌ Class component
- ❌ Missing prop types

---

### Test 3: Python & FastAPI (Rule 3)

**Ask Cursor:**
```
Create a FastAPI route that returns a list of items
```

**Expected (Rule 3 working):**
- ✅ Uses `async def`
- ✅ Type hints on function and parameters
- ✅ Uses `Annotated[Type, Depends(...)]` for dependencies
- ✅ Has `response_model` in decorator
- ✅ Proper HTTP status codes

**If it doesn't:**
- ❌ Synchronous function
- ❌ No type hints
- ❌ Old-style dependency injection
- ❌ Missing response_model

---

### Test 4: Security & Blockchain (Rule 4)

**Ask Cursor:**
```
How should I store API keys in my application?
```

**Expected (Rule 4 working):**
- ✅ Should say NEVER store in code
- ✅ Recommends environment variables
- ✅ Mentions key management services (KMS, Vault)
- ✅ Warns against hardcoding
- ✅ Suggests secure storage methods

**If it doesn't:**
- ❌ Suggests storing in code
- ❌ Doesn't warn about security
- ❌ Suggests hardcoding keys

---

### Test 5: Testing & Documentation (Rule 5)

**Ask Cursor:**
```
Write a test for a function that validates an email address
```

**Expected (Rule 5 working):**
- ✅ Clear test structure (Arrange-Act-Assert)
- ✅ Descriptive test name
- ✅ Tests edge cases
- ✅ Proper assertions
- ✅ Well-organized test code

**If it doesn't:**
- ❌ Unclear test structure
- ❌ Poor naming
- ❌ Missing edge cases
- ❌ Weak assertions

---

## 🔍 Advanced Verification Tests

### MCP Awareness Test

**Ask Cursor:**
```
How can I search for React documentation?
```

**Expected (MCP rules working):**
- ✅ Mentions using `context7` MCP
- ✅ Suggests MCP tools
- ✅ References available MCPs

### Extension Awareness Test

**Ask Cursor:**
```
What tools can help me find TypeScript errors?
```

**Expected (Extension rules working):**
- ✅ Mentions Error Lens extension
- ✅ Mentions ESLint
- ✅ References extension capabilities

### Code Style Test

**Ask Cursor:**
```
Write a Python function to validate an Ethereum address
```

**Expected (All rules working):**
- ✅ Type hints
- ✅ Async if needed
- ✅ Security-focused (validates address)
- ✅ Error handling
- ✅ Docstring
- ✅ Uses `eth_utils` or similar (validates properly)

---

## 🎯 Quick Verification Checklist

Run these quick tests in order:

1. [ ] **TypeScript Test**: Create React component → Should use TypeScript, functional, no `any`
2. [ ] **FastAPI Test**: Create route → Should use async, type hints, Depends pattern
3. [ ] **Security Test**: Ask about API keys → Should warn against storing in code
4. [ ] **Error Handling Test**: Create function → Should include error handling
5. [ ] **Documentation Test**: Create function → Should include docstring

**If 4/5 pass**: Rules are working! ✅  
**If 2-3 pass**: Some rules working, may need restart  
**If 0-1 pass**: Rules may not be applied, check settings

---

## 🔧 Troubleshooting

### Rules Not Working?

1. **Restart Cursor** (required after adding rules)
   - Close Cursor completely
   - Reopen Cursor
   - Rules should be active

2. **Check Settings**
   - Go to Settings → Rules
   - Verify all 5 rules are present
   - Check that rules are saved (not just typed)

3. **Verify Format**
   - Rules should be markdown (not wrapped in code blocks)
   - Code examples should use triple backticks
   - Headers should use #, ##, ###

4. **Clear Cache** (if needed)
   - Close Cursor
   - Clear Cursor cache (if issues persist)
   - Restart

### Partial Rules Working?

- Some rules may take effect immediately
- Others may need context (e.g., working in TypeScript file)
- Try opening relevant file type (`.tsx`, `.py`) and testing

---

## ✅ Success Indicators

You'll know rules are working when:

1. ✅ Code suggestions match your style preferences
2. ✅ TypeScript code has proper types (no `any`)
3. ✅ Python code has type hints
4. ✅ Security questions get security-focused answers
5. ✅ Code includes error handling
6. ✅ Functions have docstrings
7. ✅ FastAPI routes use dependency injection pattern

---

**Test these and let me know which ones pass!** 🚀
