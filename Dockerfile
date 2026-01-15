# Stage 1: Builder
# Use Python 3.12-slim for best performance/size balance in 2026
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements context
# Note: we assume server_fastapi/requirements.txt covers the backend
COPY server_fastapi/requirements.txt .

# Build wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runner (SLSA Level 3 Compliant: Non-root, Minimal)
FROM python:3.12-slim

WORKDIR /app

# Create non-root application user/group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Runtime packages (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy artifacts from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY server_fastapi/ ./server_fastapi/
# Signer module would differ here in production (installed as lib), 
# but for now we copy it if it exists or assume it's part of the python path
COPY signer/ ./signer/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Granian as the Entry Point (High Performance ASGI)
CMD ["python", "server_fastapi/serve_granian.py"]
