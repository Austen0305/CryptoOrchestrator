"""
Prometheus Metrics Endpoint
Provides comprehensive metrics for monitoring and observability
"""
from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import psutil
import os
from typing import Dict, Any

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# HTTP Metrics (using unique prefixes to avoid conflicts)
crypto_http_requests_total = Counter(
    'crypto_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

crypto_http_request_duration_seconds = Histogram(
    'crypto_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database Metrics (using unique prefixes)
crypto_db_connections_active = Gauge(
    'crypto_db_connections_active',
    'Active database connections'
)

crypto_db_connections_idle = Gauge(
    'crypto_db_connections_idle',
    'Idle database connections'
)

# Redis Metrics (using unique prefixes)
crypto_redis_connections_active = Gauge(
    'crypto_redis_connections_active',
    'Active Redis connections'
)

crypto_redis_cache_hits = Counter(
    'crypto_redis_cache_hits_total',
    'Total Redis cache hits'
)

crypto_redis_cache_misses = Counter(
    'crypto_redis_cache_misses_total',
    'Total Redis cache misses'
)

# ML Model Metrics (using unique prefixes)
crypto_ml_model_inference_total = Counter(
    'crypto_ml_model_inference_total',
    'Total ML model inferences',
    ['model_type']
)

crypto_ml_model_inference_duration_seconds = Histogram(
    'crypto_ml_model_inference_duration_seconds',
    'ML model inference duration in seconds',
    ['model_type']
)

# Trading Bot Metrics (using unique prefixes)
crypto_trading_bots_active = Gauge(
    'crypto_trading_bots_active',
    'Number of active trading bots'
)

crypto_trades_total = Counter(
    'crypto_trades_total',
    'Total trades executed',
    ['exchange', 'symbol', 'side']
)

# WebSocket Metrics (using unique prefixes)
crypto_websocket_connections_active = Gauge(
    'crypto_websocket_connections_active',
    'Active WebSocket connections'
)

crypto_websocket_messages_total = Counter(
    'crypto_websocket_messages_total',
    'Total WebSocket messages',
    ['type']
)

# System Metrics (using unique prefixes)
crypto_system_cpu_percent = Gauge(
    'crypto_system_cpu_percent',
    'System CPU usage percentage'
)

crypto_system_memory_bytes = Gauge(
    'crypto_system_memory_bytes',
    'System memory usage in bytes',
    ['type']  # 'used', 'available', 'total'
)

crypto_system_disk_bytes = Gauge(
    'crypto_system_disk_bytes',
    'System disk usage in bytes',
    ['path', 'type']  # 'used', 'free', 'total'
)


@router.get("", response_class=Response)
async def get_metrics():
    """
    Prometheus metrics endpoint
    Returns metrics in Prometheus format
    """
    # Update system metrics
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        crypto_system_cpu_percent.set(cpu_percent)
        
        # Memory
        memory = psutil.virtual_memory()
        crypto_system_memory_bytes.labels(type='used').set(memory.used)
        crypto_system_memory_bytes.labels(type='available').set(memory.available)
        crypto_system_memory_bytes.labels(type='total').set(memory.total)
        
        # Disk
        disk = psutil.disk_usage('/')
        crypto_system_disk_bytes.labels(path='/', type='used').set(disk.used)
        crypto_system_disk_bytes.labels(path='/', type='free').set(disk.free)
        crypto_system_disk_bytes.labels(path='/', type='total').set(disk.total)
    except Exception:
        # Silently fail if system metrics unavailable
        pass
    
    # Generate Prometheus metrics
    metrics_data = generate_latest()
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Human-readable metrics summary
    Returns key metrics in JSON format
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except Exception:
        memory = None
        disk = None
        cpu_percent = None
    
    return {
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "used_bytes": memory.used if memory else None,
                "available_bytes": memory.available if memory else None,
                "total_bytes": memory.total if memory else None,
                "percent": memory.percent if memory else None
            },
            "disk": {
                "used_bytes": disk.used if disk else None,
                "free_bytes": disk.free if disk else None,
                "total_bytes": disk.total if disk else None,
                "percent": disk.percent if disk else None
            }
        },
        "metrics": {
            "http_requests": "See /metrics for detailed HTTP metrics",
            "database": "See /metrics for database connection metrics",
            "redis": "See /metrics for Redis cache metrics",
            "ml_models": "See /metrics for ML model inference metrics",
            "trading_bots": "See /metrics for trading bot metrics",
            "websockets": "See /metrics for WebSocket metrics"
        }
    }

