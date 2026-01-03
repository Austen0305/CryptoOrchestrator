# Testing Docker Optimization

**Date:** January 2, 2026  
**Purpose:** Verify optimized Docker build works correctly

---

## 🧪 Test Plan

### Prerequisites

1. **Enable BuildKit** (required for optimizations)
   ```bash
   export DOCKER_BUILDKIT=1
   export COMPOSE_DOCKER_CLI_BUILD=1
   ```

2. **Verify files exist:**
   - `Dockerfile.optimized`
   - `requirements-base.txt`
   - `requirements-ml.txt`

### Test 1: Build Without ML (Fast)

**Goal:** Verify build works without ML dependencies

```bash
# Build without ML
docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=false \
  -t cryptoorchestrator:test-no-ml .

# Test if it runs
docker run --rm cryptoorchestrator:test-no-ml \
  python -c "import fastapi; print('FastAPI works!')"

# Verify ML packages are missing (expected)
docker run --rm cryptoorchestrator:test-no-ml \
  python -c "import tensorflow" 2>&1
# Should show: "No module named 'tensorflow'"
```

**Expected:**
- ✅ Build succeeds in ~5-7 minutes (first time)
- ✅ Image runs correctly
- ✅ FastAPI and core packages work
- ✅ TensorFlow/PyTorch are missing (expected)

### Test 2: Build With ML (Full)

**Goal:** Verify build works with ML dependencies

```bash
# Build with ML
docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=true \
  -t cryptoorchestrator:test-with-ml .

# Test if it runs
docker run --rm cryptoorchestrator:test-with-ml \
  python -c "import fastapi; print('FastAPI works!')"

# Verify ML packages are present
docker run --rm cryptoorchestrator:test-with-ml \
  python -c "import tensorflow; print('TensorFlow:', tensorflow.__version__)"
```

**Expected:**
- ✅ Build succeeds in ~12-15 minutes (first time)
- ✅ Image runs correctly
- ✅ FastAPI and core packages work
- ✅ TensorFlow/PyTorch are present

### Test 3: Cache Effectiveness

**Goal:** Verify BuildKit cache mounts work

```bash
# First build (no cache)
time docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=false \
  -t cryptoorchestrator:test-no-ml .

# Second build (should use cache)
time docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=false \
  -t cryptoorchestrator:test-no-ml .
```

**Expected:**
- ✅ First build: ~5-7 minutes
- ✅ Second build: ~1-2 minutes (85-90% faster)

### Test 4: Image Size Comparison

**Goal:** Verify ML dependencies increase image size

```bash
# Check image sizes
docker images cryptoorchestrator:test-no-ml
docker images cryptoorchestrator:test-with-ml
```

**Expected:**
- ✅ Without ML: ~2-3GB
- ✅ With ML: ~8-10GB

---

## 🚀 Quick Test Script

Use the automated test script:

```bash
# Make executable (if needed)
chmod +x scripts/docker/test-optimized-build.sh

# Run tests
./scripts/docker/test-optimized-build.sh
```

This script will:
1. ✅ Check all required files exist
2. ✅ Build without ML dependencies
3. ✅ Build with ML dependencies
4. ✅ Test both images run correctly
5. ✅ Verify ML packages presence/absence
6. ✅ Compare image sizes
7. ✅ Test cache effectiveness

---

## 🔍 Manual Testing Steps

### Step 1: Test Base Build

```bash
cd /home/labarcodez/CryptoOrchestrator

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build without ML
docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=false \
  -t cryptoorchestrator:test \
  .
```

**Check for:**
- ✅ Build completes successfully
- ✅ No errors about missing files
- ✅ Build time is reasonable (~5-7 min first time)

### Step 2: Test Image Runs

```bash
# Test basic import
docker run --rm cryptoorchestrator:test \
  python -c "import fastapi; print('OK')"

# Test FastAPI app structure
docker run --rm cryptoorchestrator:test \
  python -c "from server_fastapi.main import app; print('App loaded')"
```

**Check for:**
- ✅ No import errors
- ✅ App loads correctly

### Step 3: Test ML Build (Optional)

```bash
# Build with ML (takes longer)
docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=true \
  -t cryptoorchestrator:test-ml \
  .

# Test ML packages
docker run --rm cryptoorchestrator:test-ml \
  python -c "import tensorflow; print('TensorFlow OK')"
```

---

## 🐛 Troubleshooting

### BuildKit Not Enabled

**Error:** `--mount=type=cache` not recognized

**Fix:**
```bash
export DOCKER_BUILDKIT=1
# Or: DOCKER_BUILDKIT=1 docker build ...
```

### Missing Requirements Files

**Error:** `requirements-base.txt not found`

**Fix:** Ensure files exist:
```bash
ls -la requirements-base.txt requirements-ml.txt
```

### Build Fails on ML Dependencies

**Error:** TensorFlow/PyTorch installation fails

**Possible causes:**
- Disk space (ML deps are huge)
- Network issues
- Python version incompatibility

**Fix:**
```bash
# Check disk space
df -h

# Try building without ML first
docker build -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=false \
  -t cryptoorchestrator:test .
```

### Cache Not Working

**Issue:** Rebuilds still slow

**Check:**
1. BuildKit enabled? (`docker buildx version`)
2. Using correct Dockerfile? (`-f Dockerfile.optimized`)
3. Cache directory accessible?

**Debug:**
```bash
# Check BuildKit status
docker buildx ls

# Build with verbose output
DOCKER_BUILDKIT=1 docker build \
  -f Dockerfile.optimized \
  --progress=plain \
  -t cryptoorchestrator:test .
```

---

## ✅ Success Criteria

All tests pass if:

1. ✅ Build without ML completes successfully
2. ✅ Build with ML completes successfully
3. ✅ Both images run correctly
4. ✅ ML packages present/absent as expected
5. ✅ Rebuild is 85-90% faster (cache works)
6. ✅ Image sizes are reasonable

---

## 📊 Expected Results

| Test | Expected Result | Status |
|------|----------------|--------|
| Build without ML | ~5-7 min (first), ~1-2 min (cached) | ⏳ |
| Build with ML | ~12-15 min (first), ~2-3 min (cached) | ⏳ |
| Image runs | No errors | ⏳ |
| ML packages | Present/absent as expected | ⏳ |
| Cache works | 85-90% faster rebuilds | ⏳ |

---

**Ready to test?** Run the test script or follow manual steps above.
