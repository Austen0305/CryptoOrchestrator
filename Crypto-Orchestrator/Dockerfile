# ==========================================
# Dockerfile for Crypto-Orchestrator FastAPI Backend
# ==========================================
# Multi-stage build for optimized production image

# Stage 1: Base image with Python
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production image
FROM base as production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY server_fastapi/ /app/server_fastapi/
COPY shared/ /app/shared/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/models

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check (using /healthz for Kubernetes compatibility)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "server_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]

