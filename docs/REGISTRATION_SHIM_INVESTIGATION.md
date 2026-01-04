# Registration Shim Middleware Investigation

**Date:** January 3, 2026  
**Status:** ✅ RESOLVED - Root Causes Fixed, Shim Removed

---

## Problem Statement

An intermittent hang affects `/api/*` routes in the deeper middleware/route stack. A registration shim middleware was created as a workaround to ensure users can create accounts and log in.

**Location:** `server_fastapi/main.py` lines 709-923

---

## ✅ RESOLUTION (January 3, 2026)

**Root Causes Identified and Fixed:**
1. RequestDeduplicationMiddleware - Redis operations without timeout
2. RequestValidationMiddleware - Body reading without timeout

**Fixes Applied:**
1. ✅ RequestDeduplicationMiddleware now skips auth endpoints
2. ✅ RequestDeduplicationMiddleware has Redis timeouts (500ms)
3. ✅ RequestValidationMiddleware now skips auth endpoints
4. ✅ RequestValidationMiddleware has body read timeout (2s)

**Shim Removed:** ✅ Registration shim middleware removed from `server_fastapi/main.py`

**Status:** ✅ RESOLVED - Normal registration route now used

---

## Potential Root Causes

### 1. Request Queue Middleware
**File:** `server_fastapi/middleware/request_queue.py`
- Queues requests when system is under load
- May cause delays if queue is full
- **Investigation:** Check if queue is blocking requests

### 2. Request Batching Middleware
**File:** `server_fastapi/middleware/request_batching.py`
- Batches requests together
- May delay individual requests waiting for batch
- **Investigation:** Check if batching is causing delays

### 3. Request Deduplication Middleware
**File:** `server_fastapi/middleware/request_deduplication.py`
- Deduplicates duplicate requests
- May cause delays if deduplication logic is slow
- **Investigation:** Check deduplication performance

### 4. Database Connection Pool Exhaustion
- All connections in use
- Requests wait for available connection
- **Investigation:** Check pool size, active connections

### 5. Redis Connection Timeout
- Redis unavailable or slow
- Middleware waiting for Redis response
- **Investigation:** Check Redis health, connection timeouts

### 6. Heavy Middleware Stack
- Too many middleware layers
- Each adds latency
- **Investigation:** Profile middleware execution time

---

## Investigation Plan

### Phase 1: Isolate the Problem

1. **Disable Heavy Middleware:**
   ```bash
   # Set in .env
   ENABLE_HEAVY_MIDDLEWARE=false
   ```

2. **Test Registration:**
   - Remove shim middleware temporarily
   - Test normal `/api/auth/register` route
   - Check if hang still occurs

3. **Enable Middleware One by One:**
   - Start with minimal middleware
   - Add middleware one at a time
   - Identify which middleware causes hang

### Phase 2: Profile Middleware

1. **Add Timing Logs:**
   - Log entry/exit of each middleware
   - Measure time spent in each middleware
   - Identify slow middleware

2. **Use Middleware Profiling:**
   - Enable performance profiling middleware
   - Review middleware execution times
   - Find bottlenecks

### Phase 3: Fix Root Cause

1. **If Request Queue:**
   - Increase queue size
   - Reduce queue timeout
   - Disable for auth endpoints

2. **If Request Batching:**
   - Exclude auth endpoints from batching
   - Reduce batch wait time
   - Disable batching for critical paths

3. **If Database Pool:**
   - Increase pool size
   - Add connection pool monitoring
   - Optimize connection usage

4. **If Redis:**
   - Check Redis health
   - Increase connection timeout
   - Add fallback for Redis unavailability

---

## Recommended Fixes

### Immediate (Keep Shim, Improve It)

1. **Add Timeout to Shim:**
   ```python
   async def registration_shim(request: Request, call_next):
       # Add timeout wrapper
       try:
           return await asyncio.wait_for(
               handle_registration(request),
               timeout=10.0
           )
       except asyncio.TimeoutError:
           return JSONResponse(
               status_code=504,
               content={"detail": "Registration timeout"}
           )
   ```

2. **Improve Error Handling:**
   - Better error messages
   - Logging for debugging
   - Retry logic for transient failures

### Short Term (Investigate Root Cause)

1. **Add Middleware Profiling:**
   - Enable performance profiling
   - Log middleware execution times
   - Identify slow middleware

2. **Test Without Heavy Middleware:**
   - Set `ENABLE_HEAVY_MIDDLEWARE=false`
   - Test if hang still occurs
   - Narrow down problematic middleware

### Long Term (Remove Shim)

1. **Fix Root Cause:**
   - Identify and fix blocking middleware
   - Optimize middleware stack
   - Remove shim once fixed

2. **Add Integration Tests:**
   - Test registration without shim
   - Verify no hangs occur
   - Monitor for regressions

---

## Testing Strategy

### 1. Load Testing

```bash
# Test registration endpoint under load
ab -n 1000 -c 10 -p register.json -T application/json \
  http://localhost:8000/api/auth/register
```

### 2. Stress Testing

```bash
# Test with many concurrent requests
for i in {1..50}; do
  curl -X POST http://localhost:8000/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test'$i'@example.com","password":"test123456"}' &
done
wait
```

### 3. Middleware Profiling

```python
# Add to middleware setup
import time

async def profile_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    if duration > 1.0:
        logger.warning(f"Slow middleware: {duration:.2f}s")
    return response
```

---

## Monitoring

### Key Metrics to Track

1. **Registration Response Time:**
   - P50, P95, P99 latencies
   - Timeout rate
   - Error rate

2. **Middleware Execution Time:**
   - Time spent in each middleware
   - Slow middleware identification
   - Queue wait times

3. **Database Connection Pool:**
   - Active connections
   - Wait time for connections
   - Pool exhaustion events

4. **Redis Health:**
   - Connection time
   - Response time
   - Error rate

---

## Recommendations

### Immediate Actions

1. ✅ **Keep Shim for Now:** It's working and ensures registration works
2. ⚠️ **Add Monitoring:** Track registration performance
3. ⚠️ **Add Timeouts:** Prevent indefinite hangs

### Short Term

1. **Investigate Middleware Stack:** Profile each middleware
2. **Test Without Heavy Middleware:** Narrow down problem
3. **Optimize Database Pool:** Ensure adequate connections

### Long Term

1. **Fix Root Cause:** Remove blocking operations
2. **Remove Shim:** Once root cause is fixed
3. **Add Tests:** Prevent regressions

---

## Related Files

- `server_fastapi/main.py` - Registration shim (lines 709-923)
- `server_fastapi/routes/auth.py` - Normal registration route (line 614)
- `server_fastapi/middleware/setup.py` - Middleware configuration
- `server_fastapi/middleware/config.py` - Middleware manager

---

**Status:** Workaround in place, investigation needed  
**Priority:** P0 (Critical)  
**Estimated Fix Time:** 4-8 hours investigation + fix
